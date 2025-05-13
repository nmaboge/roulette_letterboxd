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
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://letterboxd.com',
            'Referer': 'https://letterboxd.com/',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
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

    def _get_film_details(self, film_data):
        """Extrait les détails d'un film depuis les données JSON."""
        try:
            return {
                'director': film_data.get('director', 'Non disponible'),
                'rating': film_data.get('rating', 'Non noté'),
                'year': str(film_data.get('year', '')),
                'synopsis': film_data.get('description', 'Synopsis non disponible')
            }
        except Exception as e:
            print(f"Erreur lors de l'extraction des détails du film: {str(e)}")
            return {
                'director': "Non disponible",
                'rating': "Non noté",
                'year': "",
                'synopsis': "Synopsis non disponible"
            }

    def _get_films_from_html(self, url):
        """Récupère la liste des films depuis la page HTML."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            if 'sign-in' in response.url:
                raise Exception("Accès refusé. La liste est probablement privée.")
            
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Extraire les films
            films = []
            poster_containers = soup.select('li.poster-container')
            
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
                    
                    # Améliorer la qualité de l'image
                    if poster_url:
                        poster_url = poster_url.replace('0-150-0-225', '0-500-0-750')
                        poster_url = poster_url.replace('0-202-0-304', '0-500-0-750')
                        poster_url = poster_url.replace('0-230-0-345', '0-500-0-750')
                    
                    films.append({
                        'name': img.get('alt', 'Sans titre'),
                        'path': link['href'],
                        'image': poster_url
                    })
                    
                except Exception as e:
                    print(f"Erreur lors de l'extraction d'un film: {str(e)}")
                    continue
            
            return films
            
        except Exception as e:
            print(f"Erreur lors de la récupération des films depuis HTML: {str(e)}")
            return []

    def get_films(self, url):
        """Récupère un film aléatoire depuis une liste Letterboxd."""
        try:
            if not self._is_valid_letterboxd_list_url(url):
                raise Exception("URL invalide. Veuillez entrer une URL de liste Letterboxd valide.")

            print(f"Récupération des films depuis: {url}")
            
            # D'abord essayer de récupérer les films depuis la page HTML
            films = self._get_films_from_html(url)
            
            if not films:
                raise Exception("Aucun film trouvé. Veuillez vérifier que la liste est publique et contient des films.")

            # Sélectionner un film aléatoire
            chosen_film = random.choice(films)
            print(f"Film choisi: {chosen_film.get('name', 'Sans titre')}")

            # Construire l'objet de retour
            film_url = urljoin(self.base_url, chosen_film.get('path', ''))
            poster_url = chosen_film.get('image', '')

            return {
                'title': chosen_film.get('name', 'Sans titre'),
                'poster': poster_url,
                'url': film_url,
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