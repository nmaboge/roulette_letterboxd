import requests
from bs4 import BeautifulSoup
import random
from urllib.parse import urljoin, urlparse, quote
import time
import json
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

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
        self.tmdb_api_key = os.environ.get('TMDB_API_KEY', '8c247ea0b4b56ed2ff7d41c9a833aa77')  # Clé API publique TMDB
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
            
            # Cas des listes personnalisées
            if path_parts[0] == 'list' and len(path_parts) >= 2:
                self.list_type = 'list'
                self.list_slug = path_parts[1]
                return True
            
            # Cas des watchlists et films
            if len(path_parts) >= 2:
                self.username = path_parts[0]
                self.list_type = path_parts[1]
                
                # Vérifier si c'est un profil privé connu
                if self.list_type == 'profile-private':
                    raise Exception("Ce profil est privé. Les listes ne sont pas accessibles.")
                
                # Vérifier le type de liste
                if self.list_type in ['watchlist', 'films']:
                    return True
            
            return False
            
        except Exception as e:
            if str(e).startswith("Ce profil"):
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
            film_grid = soup.select_one('.poster-list')
        
        if not film_grid:
            raise Exception("Impossible d'accéder au contenu de la liste. Une connexion est probablement requise.")
        
        # Rechercher les films avec différents sélecteurs
        selectors = [
            'li.poster-container',
            'div.film-poster',
            '.poster-list li',
            '.poster-container'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"\nUtilisation du sélecteur: {selector}")
                print(f"Éléments trouvés: {len(elements)}")
                
                for element in elements:
                    try:
                        # Extraire les données du film
                        film_link = element.select_one('div.film-poster') or element.select_one('a')
                        if not film_link:
                            continue
                        
                        # Extraire l'URL du film
                        film_path = film_link.get('data-target-link') or film_link.get('href', '')
                        if not film_path:
                            continue
                        
                        # Extraire le titre
                        title = element.get('data-film-name') or element.get('data-film-slug', '')
                        if not title:
                            img = element.select_one('img')
                            if img:
                                title = img.get('alt', '')
                        
                        # Nettoyer le titre
                        title = title.replace('-', ' ').title()
                        
                        # Extraire l'ID du film et construire l'URL du poster
                        film_id = film_path.strip('/').split('/')[-1]
                        poster_url = f"https://a.ltrbxd.com/resized/film-poster/{film_id}/0/500/0-750-0-70-crop.jpg"
                        
                        film_data = {
                            'name': title or 'Sans titre',
                            'path': film_path,
                            'image': poster_url
                        }
                        
                        if film_data not in films:
                            films.append(film_data)
                            print(f"Film trouvé: {film_data['name']}")
                        
                    except Exception as e:
                        print(f"Erreur lors de l'extraction d'un film: {str(e)}")
                        continue
                
                if films:
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

    def _get_films_from_api(self, username, list_type):
        """Tente de récupérer les films via l'API AJAX de Letterboxd."""
        try:
            # Construire l'URL de base
            base_url = f"https://letterboxd.com/{username}/"
            if list_type == 'watchlist':
                base_url += "watchlist/"
            elif list_type == 'films':
                base_url += "films/"
            else:
                return None

            all_films = []
            page = 1
            has_more_pages = True
            seen_films = set()  # Pour éviter les doublons

            while has_more_pages:
                # Construire l'URL de la page
                page_url = f"{base_url}page/{page}/" if page > 1 else base_url
                print(f"\nRécupération de la page {page}: {page_url}")
                
                try:
                    # Faire la requête
                    response = self.session.get(page_url, timeout=10)
                    response.raise_for_status()
                    
                    # Vérifier l'accessibilité de la page
                    self._check_page_accessibility(response)
                    
                    # Parser le HTML
                    soup = BeautifulSoup(response.text, 'html5lib')
                    
                    # Trouver tous les films sur la page
                    film_elements = soup.select('li.poster-container')
                    
                    if not film_elements:
                        print("Aucun film trouvé sur cette page")
                        has_more_pages = False
                        continue
                    
                    print(f"Films trouvés sur la page {page}: {len(film_elements)}")
                    
                    # Extraire les informations de chaque film
                    for container in film_elements:
                        try:
                            film_link = container.select_one('div.film-poster')
                            if not film_link:
                                continue
                            
                            # Extraire l'URL du film
                            film_path = film_link.get('data-target-link', '')
                            if not film_path:
                                link_element = container.select_one('a')
                                if link_element:
                                    film_path = link_element.get('href', '')
                            
                            if not film_path:
                                continue
                            
                            # Vérifier si nous avons déjà vu ce film
                            if film_path in seen_films:
                                continue
                            
                            seen_films.add(film_path)
                            
                            # Extraire le titre
                            title = container.get('data-film-name', '')
                            if not title:
                                img = container.select_one('img')
                                if img:
                                    title = img.get('alt', '')
                            
                            # Extraire l'URL du poster
                            img = container.select_one('img')
                            if img:
                                # Essayer d'abord les attributs standards
                                poster_url = img.get('src', '') or img.get('data-src', '')
                                
                                # Nettoyer l'URL si elle commence par @
                                if poster_url and poster_url.startswith('@'):
                                    poster_url = poster_url[1:]
                                
                                # Si pas d'URL ou poster vide, construire l'URL avec l'ID du film
                                if not poster_url or 'empty-poster' in poster_url:
                                    film_id = film_path.strip('/').split('/')[-1]
                                    # Utiliser l'API AJAX de Letterboxd
                                    poster_url = f"https://letterboxd.com/ajax/poster/film/{film_id}/std/300x450/"
                            else:
                                # Si pas d'image trouvée, utiliser une image par défaut
                                poster_url = 'https://via.placeholder.com/300x450?text=Pas+d%27image'
                            
                            film_data = {
                                'name': title or 'Sans titre',
                                'path': film_path,
                                'image': poster_url
                            }
                            
                            all_films.append(film_data)
                            print(f"Film trouvé: {film_data['name']}")
                            
                        except Exception as e:
                            print(f"Erreur lors de l'extraction d'un film: {str(e)}")
                            continue
                    
                    # Vérifier s'il y a une page suivante
                    next_page = soup.select_one('a.next')
                    if not next_page:
                        has_more_pages = False
                    else:
                        page += 1
                        # Ajouter un petit délai pour éviter de surcharger le serveur
                        time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Erreur lors de la récupération de la page {page}: {str(e)}")
                    has_more_pages = False
            
            if all_films:
                print(f"\nNombre total de films uniques trouvés: {len(all_films)}")
                return {'films': all_films}
            
            return None
            
        except Exception as e:
            print(f"Erreur lors de l'appel à l'API: {str(e)}")
            return None

    def _get_tmdb_poster(self, title, year=None):
        """Récupère le poster d'un film depuis TMDB."""
        try:
            # Rechercher le film sur TMDB
            search_url = f"https://api.themoviedb.org/3/search/movie"
            params = {
                'api_key': self.tmdb_api_key,
                'query': title,
                'language': 'fr-FR'
            }
            if year:
                params['year'] = year

            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data['results']:
                # Prendre le premier résultat
                movie = data['results'][0]
                if movie.get('poster_path'):
                    # Construire l'URL du poster
                    return f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
            
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération du poster TMDB: {str(e)}")
            return None

    def _get_film_details(self, film_url):
        """Récupère les détails d'un film depuis sa page."""
        try:
            print(f"\nRécupération des détails du film: {film_url}")
            response = self.session.get(film_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Extraire les informations de base
            title = soup.select_one('h1.headline-1')
            title = title.text.strip() if title else "Sans titre"
            
            # Extraire l'année
            year = ""
            year_element = soup.select_one('a[href*="/films/year/"]')
            if year_element:
                year = year_element.text.strip()
            
            # Extraire le réalisateur
            director = "Non disponible"
            director_element = soup.select_one('a[href*="/director/"]')
            if director_element:
                director = director_element.text.strip()
            
            # Extraire la note
            rating = "Non noté"
            rating_element = soup.select_one('meta[name="twitter:data2"]')
            if rating_element:
                rating = rating_element.get('content', 'Non noté')
            
            # Récupérer le poster depuis TMDB
            poster_url = self._get_tmdb_poster(title, year)
            if not poster_url:
                # Si pas de poster TMDB, utiliser une image par défaut
                poster_url = 'https://via.placeholder.com/300x450?text=Pas+d%27image'
            
            return {
                'title': title,
                'year': year,
                'director': director,
                'rating': rating,
                'poster': poster_url
            }
            
        except Exception as e:
            print(f"Erreur lors de la récupération des détails du film: {str(e)}")
            return None

    def get_films(self, url):
        """Récupère un film aléatoire depuis une liste Letterboxd."""
        try:
            print(f"\nRécupération des films depuis: {url}")
            
            # Extraire le type de liste et le username/slug de l'URL
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            # Cas des listes personnalisées
            if len(path_parts) >= 3 and path_parts[1] == 'list':
                self.list_type = 'list'
                self.username = path_parts[0]
                self.list_slug = path_parts[2]
                # Reconstruire l'URL proprement
                url = f"{parsed.scheme}://{parsed.netloc}/{path_parts[0]}/list/{path_parts[2]}"
            else:
                self.username = path_parts[0]
                self.list_type = path_parts[1]
            
            # Essayer d'abord l'API pour les watchlists et les films
            if hasattr(self, 'username') and hasattr(self, 'list_type'):
                api_data = self._get_films_from_api(self.username, self.list_type)
                if api_data and 'films' in api_data:
                    films = api_data['films']
                    if not films:
                        raise Exception("Aucun film trouvé dans cette liste.")
                    
                    # Mélanger la liste des films pour une meilleure distribution aléatoire
                    random.shuffle(films)
                    
                    # Sélectionner un film aléatoire
                    chosen_film = random.choice(films)
                    print(f"\nFilm choisi: {chosen_film.get('name', 'Sans titre')}")
                    print(f"Nombre total de films dans la liste: {len(films)}")
                    
                    # Récupérer les détails du film
                    film_url = urljoin(self.base_url, chosen_film.get('path', ''))
                    film_details = self._get_film_details(film_url)
                    
                    if film_details:
                        return {
                            'title': film_details['title'],
                            'poster': film_details['poster'] or chosen_film.get('image', ''),
                            'url': film_url,
                            'director': film_details['director'],
                            'rating': film_details['rating'],
                            'year': film_details['year']
                        }
                    else:
                        return {
                            'title': chosen_film.get('name', 'Sans titre'),
                            'poster': chosen_film.get('image', ''),
                            'url': film_url,
                            'director': "Non disponible",
                            'rating': "Non noté",
                            'year': ""
                        }
            
            # Si l'API ne fonctionne pas, essayer la méthode HTML classique
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
            
            # Extraire les films via HTML
            films = self._extract_films_from_html(response.text)
            
            if not films:
                raise Exception("Impossible d'extraire les films de cette liste. Vérifiez qu'elle contient des films et qu'elle est publique.")

            # Sélectionner un film aléatoire
            chosen_film = random.choice(films)
            print(f"\nFilm choisi: {chosen_film.get('name', 'Sans titre')}")
            
            # Récupérer les détails du film
            film_url = urljoin(self.base_url, chosen_film.get('path', ''))
            film_details = self._get_film_details(film_url)
            
            if film_details:
                return {
                    'title': film_details['title'],
                    'poster': film_details['poster'] or chosen_film.get('image', ''),
                    'url': film_url,
                    'director': film_details['director'],
                    'rating': film_details['rating'],
                    'year': film_details['year']
                }
            else:
                return {
                    'title': chosen_film.get('name', 'Sans titre'),
                    'poster': chosen_film.get('image', ''),
                    'url': film_url,
                    'director': "Non disponible",
                    'rating': "Non noté",
                    'year': ""
                }

        except requests.RequestException as e:
            print(f"\nErreur de requête: {str(e)}")
            raise Exception(f"Erreur de connexion: {str(e)}")
        except Exception as e:
            print(f"\nErreur générale: {str(e)}")
            raise Exception(str(e)) 