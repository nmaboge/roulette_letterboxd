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
            
            # Vérifier si c'est un profil privé connu
            if self.list_type == 'profile-private':
                raise Exception("Ce profil est privé. Les listes ne sont pas accessibles.")
            
            if len(path_parts) > 2:
                self.list_slug = path_parts[2]
            
            # Vérifier le type de liste
            valid = (
                (len(path_parts) == 2 and path_parts[1] in ['watchlist', 'films']) or
                (len(path_parts) >= 3 and path_parts[1] == 'list')
            )
            
            if not valid:
                raise Exception("Type de liste non supporté. Utilisez 'watchlist', 'films' ou une liste personnalisée.")
                
            return valid
            
        except Exception as e:
            if str(e).startswith("Type de liste") or str(e).startswith("Ce profil"):
                raise
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
        
        # Vérifier si nous sommes sur une version limitée de la page
        if soup.select('.sign-in-message') or soup.select('.sign-in-overlay'):
            raise Exception("Cette liste nécessite une connexion pour voir les films.")
            
        # Détecter les messages d'erreur spécifiques
        error_messages = [
            "You must be signed in to view this content",
            "You must be logged in",
            "Sign in to Letterboxd",
            "Please sign in to access this feature"
        ]
        for message in error_messages:
            if message.lower() in html_content.lower():
                raise Exception("Cette liste nécessite une connexion pour voir les films.")
        
        # Analyser la structure HTML
        all_classes = self._analyze_html_structure(soup)
        
        # Vérifier si nous avons accès au contenu complet
        film_grid = soup.select_one('.films-grid')
        if not film_grid:
            raise Exception("Impossible d'accéder au contenu de la liste. Une connexion est probablement requise.")
        
        # Méthode 1: Recherche des conteneurs de posters avec données lazy-load
        poster_containers = soup.select('li.poster-container')
        print(f"\nMéthode 1 - Conteneurs de posters trouvés: {len(poster_containers)}")
        
        for container in poster_containers:
            try:
                # Chercher le lien du film et les données
                film_link = container.select_one('div.film-poster')
                if not film_link:
                    continue
                
                # Extraire l'URL du film depuis data-target-link
                film_path = film_link.get('data-target-link', '')
                if not film_path:
                    # Fallback sur le lien direct
                    link_element = container.select_one('a')
                    if link_element:
                        film_path = link_element.get('href', '')
                
                if not film_path:
                    continue
                
                # Extraire le titre du film
                title = container.get('data-film-name', '')
                if not title:
                    # Fallback sur l'attribut alt de l'image
                    img = container.select_one('img')
                    if img:
                        title = img.get('alt', '')
                
                # Extraire l'URL du poster
                img = container.select_one('img')
                if img:
                    poster_url = img.get('src', '') or img.get('data-src', '')
                    # Si c'est une image vide, essayer de construire l'URL du poster
                    if 'empty-poster' in poster_url:
                        film_id = film_path.strip('/').split('/')[-1]
                        poster_url = f"https://a.ltrbxd.com/resized/film-poster/{film_id}/0/500/0-750-0-70-crop.jpg"
                else:
                    poster_url = ''
                
                # Améliorer la qualité de l'image
                poster_url = self._improve_image_quality(poster_url)
                
                film_data = {
                    'name': title or 'Sans titre',
                    'path': film_path,
                    'image': poster_url
                }
                
                if film_data not in films:  # Éviter les doublons
                    films.append(film_data)
                    print(f"Film trouvé: {film_data['name']}")
                
            except Exception as e:
                print(f"Erreur lors de l'extraction d'un film: {str(e)}")
                continue
        
        # Si aucun film n'a été trouvé avec la première méthode, essayer les autres méthodes
        if not films:
            print("\nAucun film trouvé avec la première méthode, tentative avec les méthodes alternatives...")
            
            # Méthode 2: Recherche directe des posters de films
            film_posters = soup.select('div.film-poster')
            print(f"Méthode 2 - Posters de films trouvés: {len(film_posters)}")
            
            # Méthode 3: Recherche des liens de films
            film_links = soup.select('div.poster a')
            print(f"Méthode 3 - Liens de films trouvés: {len(film_links)}")
            
            # Méthode 4: Recherche générique d'images de films
            film_images = soup.select('img[src*="film-poster"], img[data-src*="film-poster"]')
            print(f"Méthode 4 - Images de films trouvées: {len(film_images)}")
            
            # Si toujours aucun film trouvé
            if not any([film_posters, film_links, film_images]):
                print("\nAucun film trouvé avec les méthodes alternatives.")
                if soup.select('.sign-in-message, .sign-in-overlay, .require-signin'):
                    raise Exception("Cette liste nécessite une connexion pour voir les films.")
                else:
                    raise Exception("Impossible d'extraire les films de cette liste. Vérifiez qu'elle contient des films et qu'elle est publique.")
        
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

    def _check_page_accessibility(self, response):
        """Vérifie si la page est accessible et fournit des informations détaillées sur les problèmes."""
        # Vérifier la redirection vers la page de connexion
        if 'sign-in' in response.url or 'login' in response.url:
            raise Exception("Cette liste nécessite une connexion. Assurez-vous que la liste est publique.")
        
        # Vérifier le contenu pour des messages spécifiques
        content_lower = response.text.lower()
        
        if "this profile is private" in content_lower or "ce profil est privé" in content_lower:
            raise Exception("Ce profil est privé. Les listes ne sont pas accessibles.")
            
        if "this list is private" in content_lower or "cette liste est privée" in content_lower:
            raise Exception("Cette liste est privée. Demandez à son propriétaire de la rendre publique.")
            
        if "you must be logged in" in content_lower or "vous devez être connecté" in content_lower:
            raise Exception("Cette liste nécessite une connexion. Assurez-vous que la liste est publique.")
            
        if "page not found" in content_lower or "page non trouvée" in content_lower:
            raise Exception("Cette liste n'existe pas. Vérifiez l'URL.")

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
            
            # Vérifier l'accessibilité de la page
            self._check_page_accessibility(response)
            
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
            raise Exception(str(e)) 