import requests
from bs4 import BeautifulSoup
import random
import re

class LetterboxdScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_films(self, url):
        """Récupère un film aléatoire depuis une watchlist Letterboxd"""
        try:
            if not url:
                raise ValueError("L'URL ne peut pas être vide")
                
            # Vérifie si l'URL est une URL de watchlist Letterboxd
            if 'letterboxd.com' not in url:
                raise ValueError("L'URL doit être une URL Letterboxd")
            
            # Fait la requête HTTP
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Parse le HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Récupère tous les films (posters)
            film_elements = soup.select('li.poster-container')
            
            if not film_elements:
                return None
            
            # Sélectionne un film aléatoire
            random_film = random.choice(film_elements)
            
            # Extraire les détails du film
            film_data = {}
            
            # Titre du film
            img = random_film.select_one('img')
            film_data['title'] = img.get('alt') if img and img.get('alt') else "Titre inconnu"
            
            # URL du poster
            film_data['poster'] = img.get('src') if img else ""
            # Dans Letterboxd, ajuster l'URL du poster pour obtenir une meilleure résolution
            film_data['poster'] = film_data['poster'].replace('0-202-0-304', '0-500-0-750') if film_data['poster'] else ""
            
            # URL du film sur Letterboxd
            film_link = random_film.select_one('div.film-poster a')
            film_data['url'] = "https://letterboxd.com" + film_link.get('href') if film_link else url
            
            # Pour récupérer plus de détails comme année, réalisateur, etc.
            # Il faut faire une deuxième requête sur la page du film
            if film_link and film_link.get('href'):
                film_data.update(self.get_film_details("https://letterboxd.com" + film_link.get('href')))
            
            return film_data
            
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des films: {str(e)}")
    
    def get_film_details(self, film_url):
        """Récupère des détails supplémentaires sur un film"""
        try:
            # Fait la requête HTTP
            response = requests.get(film_url, headers=self.headers)
            response.raise_for_status()
            
            # Parse le HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {}
            
            # Année
            year_element = soup.select_one('small.number')
            details['year'] = year_element.text.strip() if year_element else ""
            
            # Réalisateur
            director_element = soup.select_one('span.prettify') or soup.select_one('meta[name="twitter:data1"]')
            if director_element:
                if director_element.get('content'):
                    details['director'] = director_element.get('content')
                else:
                    details['director'] = director_element.text.strip()
            else:
                details['director'] = "Réalisateur inconnu"
            
            # Note moyenne
            rating_element = soup.select_one('meta[name="twitter:data2"]')
            details['rating'] = rating_element.get('content', '') if rating_element else ""
            
            # Synopsis
            synopsis_element = soup.select_one('div.review-ignore-wrap > div.truncate') or soup.select_one('meta[name="description"]') 
            if synopsis_element:
                if synopsis_element.get('content'):
                    details['synopsis'] = synopsis_element.get('content')
                else:
                    details['synopsis'] = synopsis_element.text.strip()
            else:
                details['synopsis'] = "Pas de synopsis disponible"
            
            return details
            
        except Exception as e:
            # Ne pas faire échouer tout le processus si les détails sont indisponibles
            print(f"Avertissement: impossible de récupérer les détails du film: {e}")
            return {
                'year': '',
                'director': 'Réalisateur inconnu',
                'rating': '',
                'synopsis': 'Pas de synopsis disponible'
            }
