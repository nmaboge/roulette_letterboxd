import requests
from bs4 import BeautifulSoup
import random
from urllib.parse import urljoin, urlparse
import time

class LetterboxdScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
                
            return (
                (len(path_parts) == 2 and path_parts[1] in ['watchlist', 'films']) or
                (len(path_parts) >= 3 and path_parts[1] == 'list')
            )
        except:
            return False

    def _get_page_count(self, soup):
        """Obtient le nombre total de pages."""
        pagination = soup.select_one('.pagination')
        if not pagination:
            return 1
        
        last_page = pagination.select('li.paginate-page')
        if not last_page:
            return 1
            
        try:
            return int(last_page[-1].get_text().strip())
        except:
            return 1

    def _extract_films_from_page(self, soup):
        """Extrait les films d'une page."""
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
                    # Remplacer les suffixes de basse qualité
                    quality_suffixes = ['_tmb', '_med', '_smd', '_md', '_std']
                    for suffix in quality_suffixes:
                        poster_url = poster_url.replace(suffix, '_lrg')
                    
                    # Ajuster les dimensions
                    poster_url = poster_url.replace('0-150-0-225', '0-500-0-750')
                    poster_url = poster_url.replace('0-202-0-304', '0-500-0-750')
                    poster_url = poster_url.replace('0-230-0-345', '0-500-0-750')
                
                films.append({
                    'title': img.get('alt', 'Sans titre'),
                    'poster': poster_url,
                    'url': film_url
                })
                
            except Exception as e:
                print(f"Erreur lors de l'extraction d'un film: {str(e)}")
                continue
                
        return films

    def _get_film_details(self, url):
        """Récupère les détails d'un film."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraire les détails
            director_elem = soup.select_one('.film-director')
            rating_elem = soup.select_one('.average-rating')
            year_elem = soup.select_one('.film-header-lockup h1.headline-1 .number')
            synopsis_elem = soup.select_one('.truncate') or soup.select_one('meta[name="description"]')
            
            return {
                'director': director_elem.get_text().strip() if director_elem else "Non disponible",
                'rating': rating_elem.get_text().strip() if rating_elem else "Non noté",
                'year': year_elem.get_text().strip() if year_elem else "",
                'synopsis': synopsis_elem.get('content', '').strip() if synopsis_elem and synopsis_elem.get('content') else 
                          synopsis_elem.get_text().strip() if synopsis_elem else "Synopsis non disponible"
            }
            
        except Exception as e:
            print(f"Erreur lors de la récupération des détails: {str(e)}")
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
            
            # Première requête pour obtenir le nombre de pages
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Obtenir le nombre total de pages
            total_pages = self._get_page_count(soup)
            
            # Choisir une page aléatoire
            random_page = random.randint(1, total_pages)
            
            # Si ce n'est pas la première page, faire une nouvelle requête
            if random_page > 1:
                page_url = f"{url}page/{random_page}/"
                response = self.session.get(page_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraire les films de la page
            films = self._extract_films_from_page(soup)
            
            if not films:
                raise Exception("Aucun film trouvé. Veuillez vérifier que la liste est publique et contient des films.")
            
            # Sélectionner un film aléatoire
            chosen_film = random.choice(films)
            
            # Récupérer les détails du film
            details = self._get_film_details(chosen_film['url'])
            
            # Combiner les informations
            return {
                'title': chosen_film['title'],
                'poster': chosen_film['poster'],
                'url': chosen_film['url'],
                'director': details['director'],
                'rating': details['rating'],
                'year': details['year'],
                'synopsis': details['synopsis']
            }
            
        except requests.RequestException as e:
            raise Exception(f"Erreur de connexion: {str(e)}")
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des films: {str(e)}") 