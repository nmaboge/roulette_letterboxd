import requests
from bs4 import BeautifulSoup
import random
from urllib.parse import urljoin, urlparse
import time
import json
import re

class LetterboxdScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://letterboxd.com',
            'Referer': 'https://letterboxd.com/',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        self.base_url = "https://letterboxd.com"
        self.api_base_url = "https://letterboxd.com/ajax"
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

    def get_films(self, url):
        """Récupère un film aléatoire depuis une liste Letterboxd."""
        try:
            if not self._is_valid_letterboxd_list_url(url):
                raise Exception("URL invalide. Veuillez entrer une URL de liste Letterboxd valide.")

            # Construire l'URL de l'API en fonction du type de liste
            if self.list_type == 'watchlist':
                api_url = f"{self.api_base_url}/films/{self.username}/watchlist/"
            elif self.list_type == 'films':
                api_url = f"{self.api_base_url}/films/{self.username}/films/"
            else:
                api_url = f"{self.api_base_url}/films/{self.username}/list/{self.list_slug}/"

            print(f"Requête API vers: {api_url}")
            
            # Ajouter des paramètres pour la pagination et le tri aléatoire
            params = {
                'perPage': '100',
                'sort': 'random',
                'format': 'json'
            }

            # Faire la requête à l'API
            response = self.session.get(api_url, params=params)
            response.raise_for_status()

            # Vérifier si nous avons été redirigés
            if 'sign-in' in response.url:
                raise Exception("Accès refusé. La liste est probablement privée.")

            try:
                data = response.json()
            except json.JSONDecodeError:
                print("Réponse non-JSON reçue:", response.text[:200])
                raise Exception("Format de réponse invalide")

            if not data or 'items' not in data:
                print("Données reçues:", data)
                raise Exception("Aucun film trouvé dans la réponse")

            films = data['items']
            if not films:
                raise Exception("Aucun film trouvé. Veuillez vérifier que la liste est publique et contient des films.")

            # Sélectionner un film aléatoire
            chosen_film = random.choice(films)
            print(f"Film choisi: {chosen_film.get('name', 'Sans titre')}")

            # Construire l'objet de retour
            film_url = urljoin(self.base_url, chosen_film.get('path', ''))
            poster_url = chosen_film.get('poster', {}).get('large', '')
            if not poster_url:
                poster_url = chosen_film.get('image', '')

            # Améliorer la qualité de l'image si possible
            if poster_url:
                poster_url = poster_url.replace('0-150-0-225', '0-500-0-750')
                poster_url = poster_url.replace('0-202-0-304', '0-500-0-750')
                poster_url = poster_url.replace('0-230-0-345', '0-500-0-750')

            return {
                'title': chosen_film.get('name', 'Sans titre'),
                'poster': poster_url,
                'url': film_url,
                'director': chosen_film.get('director', {}).get('name', 'Non disponible'),
                'rating': str(chosen_film.get('rating', 'Non noté')),
                'year': str(chosen_film.get('year', '')),
                'synopsis': chosen_film.get('description', 'Synopsis non disponible')
            }

        except requests.RequestException as e:
            print(f"Erreur de requête: {str(e)}")
            raise Exception(f"Erreur de connexion: {str(e)}")
        except Exception as e:
            print(f"Erreur générale: {str(e)}")
            raise Exception(f"Erreur lors de la récupération des films: {str(e)}") 