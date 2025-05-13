import requests
from bs4 import BeautifulSoup
import random
from urllib.parse import urljoin, urlparse, quote
import time
import json
import re

class LetterboxdScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Upgrade-Insecure-Requests': '1'
        }
        self.base_url = "https://letterboxd.com"
        self.session = requests.Session()
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

    def _extract_films_from_html(self, html_content):
        """Extrait les films depuis le contenu HTML avec plusieurs méthodes."""
        films = []
        soup = BeautifulSoup(html_content, 'html5lib')
        
        print("Analyse de la page HTML...")
        
        # Méthode 1: Recherche des conteneurs de posters
        poster_containers = soup.select('li.poster-container')
        print(f"Méthode 1 - Conteneurs de posters trouvés: {len(poster_containers)}")
        
        # Méthode 2: Recherche directe des posters de films
        film_posters = soup.select('div.film-poster')
        print(f"Méthode 2 - Posters de films trouvés: {len(film_posters)}")
        
        # Méthode 3: Recherche des liens de films
        film_links = soup.select('div.film-poster > a')
        print(f"Méthode 3 - Liens de films trouvés: {len(film_links)}")
        
        # Essayer d'abord la méthode 1
        if poster_containers:
            print("Utilisation de la méthode 1...")
            for container in poster_containers:
                try:
                    link = container.select_one('div.film-poster a')
                    if not link:
                        continue
                        
                    img = link.select_one('img')
                    if not img:
                        continue
                    
                    film_url = urljoin(self.base_url, link['href'])
                    poster_url = img.get('src', '')
                    if not poster_url:
                        poster_url = img.get('data-src', '')
                    
                    if not poster_url:
                        continue
                    
                    # Améliorer la qualité de l'image
                    poster_url = self._improve_image_quality(poster_url)
                    
                    films.append({
                        'name': img.get('alt', 'Sans titre'),
                        'path': link['href'],
                        'image': poster_url
                    })
                except Exception as e:
                    print(f"Erreur lors de l'extraction d'un film (méthode 1): {str(e)}")
                    continue
        
        # Si la méthode 1 n'a pas fonctionné, essayer la méthode 2
        if not films and film_posters:
            print("Utilisation de la méthode 2...")
            for poster in film_posters:
                try:
                    link = poster.find('a')
                    if not link:
                        continue
                        
                    img = poster.find('img')
                    if not img:
                        continue
                    
                    film_url = urljoin(self.base_url, link['href'])
                    poster_url = img.get('src', '')
                    if not poster_url:
                        poster_url = img.get('data-src', '')
                    
                    if not poster_url:
                        continue
                    
                    # Améliorer la qualité de l'image
                    poster_url = self._improve_image_quality(poster_url)
                    
                    films.append({
                        'name': img.get('alt', 'Sans titre'),
                        'path': link['href'],
                        'image': poster_url
                    })
                except Exception as e:
                    print(f"Erreur lors de l'extraction d'un film (méthode 2): {str(e)}")
                    continue
        
        # Si aucune méthode n'a fonctionné, essayer la méthode 3
        if not films and film_links:
            print("Utilisation de la méthode 3...")
            for link in film_links:
                try:
                    img = link.find('img')
                    if not img:
                        continue
                    
                    film_url = urljoin(self.base_url, link['href'])
                    poster_url = img.get('src', '')
                    if not poster_url:
                        poster_url = img.get('data-src', '')
                    
                    if not poster_url:
                        continue
                    
                    # Améliorer la qualité de l'image
                    poster_url = self._improve_image_quality(poster_url)
                    
                    films.append({
                        'name': img.get('alt', 'Sans titre'),
                        'path': link['href'],
                        'image': poster_url
                    })
                except Exception as e:
                    print(f"Erreur lors de l'extraction d'un film (méthode 3): {str(e)}")
                    continue
        
        print(f"Nombre total de films trouvés: {len(films)}")
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

            print(f"Récupération des films depuis: {url}")
            
            # Faire la requête HTTP
            response = self.session.get(url)
            response.raise_for_status()
            
            # Vérifier si nous sommes redirigés vers la page de connexion
            if 'sign-in' in response.url:
                raise Exception("Accès refusé. La liste est probablement privée.")
            
            # Extraire les films
            films = self._extract_films_from_html(response.text)
            
            if not films:
                # Afficher une partie du HTML pour le débogage
                print("Contenu HTML reçu (premiers 500 caractères):")
                print(response.text[:500])
                raise Exception("Aucun film trouvé. Veuillez vérifier que la liste est publique et contient des films.")

            # Sélectionner un film aléatoire
            chosen_film = random.choice(films)
            print(f"Film choisi: {chosen_film.get('name', 'Sans titre')}")

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
            print(f"Erreur de requête: {str(e)}")
            raise Exception(f"Erreur de connexion: {str(e)}")
        except Exception as e:
            print(f"Erreur générale: {str(e)}")
            raise Exception(f"Erreur lors de la récupération des films: {str(e)}") 