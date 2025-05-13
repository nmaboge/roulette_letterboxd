import requests
from bs4 import BeautifulSoup
import random
from urllib.parse import urljoin, urlparse
import time
import json

class LetterboxdScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
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
        try:
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
        except Exception as e:
            print(f"Erreur lors de la récupération du nombre de pages: {str(e)}")
            return 1

    def _extract_films_from_page(self, soup):
        """Extrait les films d'une page."""
        films = []
        try:
            # Essayer d'abord les conteneurs de posters
            poster_containers = soup.select('li.poster-container')
            
            # Si aucun poster n'est trouvé, essayer une autre structure possible
            if not poster_containers:
                poster_containers = soup.select('.film-poster')
            
            # Si toujours rien, essayer une autre structure
            if not poster_containers:
                poster_containers = soup.select('.poster')
            
            print(f"Nombre de conteneurs trouvés: {len(poster_containers)}")
            
            for container in poster_containers:
                try:
                    # Essayer différentes structures possibles pour trouver le lien et l'image
                    link = container.select_one('div.film-poster a') or container.select_one('a') or container
                    if hasattr(link, 'get') and link.get('href'):
                        film_url = urljoin(self.base_url, link['href'])
                    else:
                        continue
                    
                    img = container.select_one('img')
                    if not img:
                        continue
                    
                    poster_url = img.get('src', '')
                    if not poster_url:
                        poster_url = img.get('data-src', '')
                    
                    if not poster_url:
                        continue
                    
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
                    
                    title = img.get('alt', 'Sans titre')
                    if not title:
                        title = img.get('title', 'Sans titre')
                    
                    films.append({
                        'title': title,
                        'poster': poster_url,
                        'url': film_url
                    })
                    
                except Exception as e:
                    print(f"Erreur lors de l'extraction d'un film: {str(e)}")
                    continue
            
            print(f"Nombre total de films extraits: {len(films)}")
            return films
            
        except Exception as e:
            print(f"Erreur lors de l'extraction des films: {str(e)}")
            return []

    def _get_film_details(self, url):
        """Récupère les détails d'un film."""
        try:
            # Ajouter un délai aléatoire pour éviter la détection
            time.sleep(random.uniform(1, 2))
            
            response = self.session.get(url)
            response.raise_for_status()
            
            # Vérifier si nous avons été redirigés vers la page de connexion
            if 'sign-in' in response.url or 'login' in response.url:
                raise Exception("Accès refusé. La liste est probablement privée.")
            
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Extraire les détails avec plusieurs sélecteurs possibles
            director_elem = (
                soup.select_one('.film-director') or 
                soup.select_one('[itemprop="director"]') or 
                soup.select_one('.director')
            )
            
            rating_elem = (
                soup.select_one('.average-rating') or 
                soup.select_one('.rating') or 
                soup.select_one('[itemprop="ratingValue"]')
            )
            
            year_elem = (
                soup.select_one('.film-header-lockup h1.headline-1 .number') or 
                soup.select_one('.year') or 
                soup.select_one('[itemprop="datePublished"]')
            )
            
            synopsis_elem = (
                soup.select_one('.truncate') or 
                soup.select_one('meta[name="description"]') or
                soup.select_one('[itemprop="description"]')
            )
            
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
            
            # Ajouter un délai aléatoire pour éviter la détection
            time.sleep(random.uniform(1, 2))
            
            # Première requête pour obtenir le nombre de pages
            response = self.session.get(url)
            response.raise_for_status()
            
            # Vérifier si nous avons été redirigés vers la page de connexion
            if 'sign-in' in response.url or 'login' in response.url:
                raise Exception("Accès refusé. La liste est probablement privée.")
            
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Obtenir le nombre total de pages
            total_pages = self._get_page_count(soup)
            print(f"Nombre total de pages: {total_pages}")
            
            # Choisir une page aléatoire
            random_page = random.randint(1, total_pages)
            print(f"Page sélectionnée: {random_page}")
            
            # Si ce n'est pas la première page, faire une nouvelle requête
            if random_page > 1:
                page_url = f"{url}page/{random_page}/"
                # Ajouter un délai aléatoire
                time.sleep(random.uniform(1, 2))
                response = self.session.get(page_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html5lib')
            
            # Extraire les films de la page
            films = self._extract_films_from_page(soup)
            
            if not films:
                raise Exception("Aucun film trouvé. Veuillez vérifier que la liste est publique et contient des films.")
            
            # Sélectionner un film aléatoire
            chosen_film = random.choice(films)
            print(f"Film choisi: {chosen_film['title']}")
            
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
            print(f"Erreur de requête: {str(e)}")
            raise Exception(f"Erreur de connexion: {str(e)}")
        except Exception as e:
            print(f"Erreur générale: {str(e)}")
            raise Exception(f"Erreur lors de la récupération des films: {str(e)}") 