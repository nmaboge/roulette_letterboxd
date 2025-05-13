import requests
from bs4 import BeautifulSoup
import random
from urllib.parse import urljoin, urlparse, quote
import time
import json
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class LetterboxdScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',  # Simplified encoding acceptance
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Connection': 'keep-alive'
        }
        self.base_url = "https://letterboxd.com"
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update(self.headers)

    def _is_valid_letterboxd_list_url(self, url):
        """Vérifie si l'URL est une liste Letterboxd valide."""
        try:
            parsed = urlparse(url)
            if parsed.netloc != "letterboxd.com":
                return False
            
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return False
            
            # Extraire le username et le type de liste
            self.username = path_parts[0]
            self.list_type = path_parts[1]
            if len(path_parts) > 2:
                self.list_slug = path_parts[2]
            
            return (
                (len(path_parts) == 2 and path_parts[1] in ['watchlist', 'films']) or
                (len(path_parts) >= 3 and path_parts[1] == 'list')
            )
        except:
            return False

    def _analyze_html_structure(self, soup):
        """Analyse la structure HTML pour le débogage."""
        print("\nAnalyse de la structure HTML:")
        
        # Vérifier la présence du conteneur principal
        main_content = soup.find('div', {'id': 'content'})
        print(f"Conteneur principal trouvé: {bool(main_content)}")
        
        # Vérifier les classes principales
        print("\nClasses principales trouvées:")
        all_classes = set()
        for tag in soup.find_all(class_=True):
            all_classes.update(tag.get('class', []))
        print(f"Nombre total de classes uniques: {len(all_classes)}")
        print("Classes pertinentes trouvées:")
        relevant_classes = ['poster-container', 'film-poster', 'poster', 'film-detail']
        for class_name in relevant_classes:
            elements = soup.find_all(class_=class_name)
            print(f"- {class_name}: {len(elements)} éléments")
        
        # Vérifier les balises img
        images = soup.find_all('img')
        print(f"\nNombre total d'images: {len(images)}")
        print("Attributs des images:")
        for img in images[:5]:  # Afficher les 5 premières images
            print(f"- alt: {img.get('alt', 'None')}")
            print(f"  src: {img.get('src', 'None')}")
            print(f"  data-src: {img.get('data-src', 'None')}")
            print("---")
        
        return all_classes

    def _extract_films_from_html(self, html_content):
        """Extrait les films depuis le contenu HTML avec plusieurs méthodes."""
        films = []
        soup = BeautifulSoup(html_content, 'html5lib')
        
        print("\nDébut de l'analyse de la page...")
        
        # Analyser la structure HTML
        all_classes = self._analyze_html_structure(soup)
        
        # Méthode 1: Recherche des conteneurs de posters
        poster_containers = soup.select('li.poster-container')
        print(f"\nMéthode 1 - Conteneurs de posters trouvés: {len(poster_containers)}")
        
        # Méthode 2: Recherche directe des posters de films
        film_posters = soup.select('div.film-poster')
        print(f"Méthode 2 - Posters de films trouvés: {len(film_posters)}")
        
        # Méthode 3: Recherche des liens de films
        film_links = soup.select('div.poster a')
        print(f"Méthode 3 - Liens de films trouvés: {len(film_links)}")
        
        # Méthode 4: Recherche générique d'images de films
        film_images = soup.select('img[src*="film-poster"], img[data-src*="film-poster"]')
        print(f"Méthode 4 - Images de films trouvées: {len(film_images)}")
        
        # Essayer toutes les méthodes dans l'ordre
        methods = [
            (poster_containers, 'li.poster-container'),
            (film_posters, 'div.film-poster'),
            (film_links, 'div.poster a'),
            (film_images, 'img[src*="film-poster"]')
        ]
        
        for elements, selector in methods:
            if elements:
                print(f"\nUtilisation du sélecteur: {selector}")
                for element in elements:
                    try:
                        # Trouver l'image et le lien selon le type d'élément
                        if element.name == 'img':
                            img = element
                            link = element.find_parent('a')
                        else:
                            link = element.find('a') if element.name != 'a' else element
                            img = element.find('img')
                        
                        if not link or not img:
                            continue
                        
                        # Extraire l'URL du film
                        film_path = link.get('href', '')
                        if not film_path:
                            continue
                        
                        # Extraire l'URL du poster
                        poster_url = img.get('src', '') or img.get('data-src', '')
                        if not poster_url:
                            continue
                        
                        # Améliorer la qualité de l'image
                        poster_url = self._improve_image_quality(poster_url)
                        
                        film_data = {
                            'name': img.get('alt', 'Sans titre'),
                            'path': film_path,
                            'image': poster_url
                        }
                        
                        if film_data not in films:  # Éviter les doublons
                            films.append(film_data)
                            print(f"Film trouvé: {film_data['name']}")
                        
                    except Exception as e:
                        print(f"Erreur lors de l'extraction d'un film: {str(e)}")
                        continue
                
                if films:  # Si nous avons trouvé des films avec cette méthode, arrêter
                    break
        
        print(f"\nNombre total de films trouvés: {len(films)}")
        return films

    def _improve_image_quality(self, poster_url):
        """Améliore la qualité de l'image du poster."""
        if not poster_url:
            return poster_url
            
        # Remplacer les suffixes de basse qualité
        quality_suffixes = ['_tmb', '_med', '_smd', '_md', '_std']
        for suffix in quality_suffixes:
            poster_url = poster_url.replace(suffix, '_lrg')
        
        # Ajuster les dimensions pour une meilleure qualité
        size_patterns = [
            ('0-150-0-225', '0-500-0-750'),
            ('0-202-0-304', '0-500-0-750'),
            ('0-230-0-345', '0-500-0-750'),
            ('0-250-0-370', '0-500-0-750'),
            ('0-380-0-570', '0-500-0-750')
        ]
        
        for old_size, new_size in size_patterns:
            poster_url = poster_url.replace(old_size, new_size)
        
        return poster_url

    def get_films(self, url):
        """Récupère un film aléatoire depuis une liste Letterboxd."""
        try:
            if not self._is_valid_letterboxd_list_url(url):
                raise Exception("URL invalide. Veuillez entrer une URL de liste Letterboxd valide.")

            print(f"\nRécupération des films depuis: {url}")
            
            # Faire la requête HTTP avec un délai
            time.sleep(1)  # Petit délai pour éviter d'être bloqué
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            print(f"Statut de la réponse: {response.status_code}")
            print(f"Type de contenu: {response.headers.get('Content-Type', 'Non spécifié')}")
            print(f"Encodage: {response.encoding}")
            print(f"En-têtes de réponse: {dict(response.headers)}")
            
            # Vérifier si nous sommes redirigés vers la page de connexion
            if 'sign-in' in response.url:
                raise Exception("Accès refusé. La liste est probablement privée.")
            
            # Force UTF-8 encoding
            response.encoding = 'utf-8'
            
            # Extraire les films
            films = self._extract_films_from_html(response.text)
            
            if not films:
                # Afficher une partie du HTML pour le débogage de manière plus lisible
                print("\nContenu HTML reçu (premiers 1000 caractères):")
                content_preview = response.text[:1000]
                # Nettoyer l'affichage pour le débogage
                content_preview = ''.join(char for char in content_preview if ord(char) >= 32 or char in '\n\r\t')
                print(content_preview)
                
                # Vérifier si la page contient des indicateurs de problèmes courants
                if "Too Many Requests" in response.text:
                    raise Exception("Trop de requêtes. Veuillez réessayer plus tard.")
                elif "CloudFlare" in response.text:
                    raise Exception("Protection CloudFlare détectée. Veuillez réessayer plus tard.")
                elif "sign in" in response.text.lower():
                    raise Exception("Cette liste nécessite une connexion.")
                else:
                    raise Exception("Aucun film trouvé. Veuillez vérifier que la liste est publique et contient des films.")

            # Sélectionner un film aléatoire
            chosen_film = random.choice(films)
            print(f"\nFilm choisi: {chosen_film.get('name', 'Sans titre')}")

            return {
                'title': chosen_film.get('name', 'Sans titre'),
                'poster': chosen_film.get('image', ''),
                'url': urljoin(self.base_url, chosen_film.get('path', '')),
                'director': "Non disponible",  # Ces informations ne sont pas disponibles dans la liste
                'rating': "Non noté",
                'year': "",
                'synopsis': "Synopsis non disponible"
            }

        except requests.RequestException as e:
            print(f"\nErreur de requête: {str(e)}")
            raise Exception(f"Erreur de connexion: {str(e)}")
        except Exception as e:
            print(f"\nErreur générale: {str(e)}")
            raise Exception(f"Erreur lors de la récupération des films: {str(e)}") 