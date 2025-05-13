from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import random
import requests
from urllib.parse import urljoin, urlparse

class LetterboxdScraper:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36")
        self.driver = None
        self.base_url = "https://letterboxd.com"

    def _is_valid_letterboxd_list_url(self, url):
        """Vérifie si l'URL est une liste Letterboxd valide."""
        try:
            parsed = urlparse(url)
            if parsed.netloc != "letterboxd.com":
                return False
            
            # Vérifier le chemin de l'URL
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return False
                
            # Les URLs valides sont :
            # /username/watchlist/
            # /username/list/list-name/
            # /username/films/
            return (
                (len(path_parts) == 2 and path_parts[1] in ['watchlist', 'films']) or
                (len(path_parts) >= 3 and path_parts[1] == 'list')
            )
        except:
            return False

    def _check_internet_connection(self):
        try:
            requests.get(self.base_url, timeout=5)
            return True
        except requests.RequestException:
            raise Exception("Impossible de se connecter à Letterboxd. Veuillez vérifier votre connexion internet.")
        
    def _setup_driver(self):
        if not self.driver:
            try:
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-setuid-sandbox')
                chrome_options.add_argument('--single-process')
                chrome_options.binary_location = "/usr/bin/chromium-browser"
                
                service = Service()
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_page_load_timeout(30)
                
                # Ajouter des variables JavaScript pour masquer l'automatisation
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': '''
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    '''
                })
            except Exception as e:
                raise Exception(f"Erreur lors de l'initialisation du navigateur: {str(e)}")

    def _cleanup_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None

    def _wait_and_scroll(self, retries=3, scroll_pause_time=2):
        for i in range(retries):
            try:
                # Scroll progressif
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                while True:
                    # Scroll jusqu'en bas
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(scroll_pause_time)
                    
                    # Calculer la nouvelle hauteur
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                
                return True
            except Exception as e:
                print(f"Erreur lors du scroll: {str(e)}")
                if i == retries - 1:
                    return False
                time.sleep(2)
        return False

    def _extract_films_from_page(self):
        films = []
        try:
            # Attendre que les films soient chargés
            time.sleep(3)
            
            # Utiliser JavaScript pour extraire les films
            films_data = self.driver.execute_script("""
                const films = [];
                // Sélectionner tous les conteneurs de films possibles
                const containers = document.querySelectorAll('.poster-container, .film-poster');
                
                containers.forEach(container => {
                    let link, img;
                    
                    // Gérer les différentes structures possibles
                    if (container.classList.contains('film-poster')) {
                        link = container.closest('a');
                        img = container.querySelector('img');
                    } else {
                        link = container.querySelector('a');
                        img = container.querySelector('img');
                    }
                    
                    if (link && img) {
                        films.push({
                            title: img.alt,
                            poster: img.src,
                            url: link.href
                        });
                    }
                });
                return films;
            """)
            
            if not films_data:
                print("Aucun film trouvé avec JavaScript, tentative avec Selenium...")
                # Méthode alternative avec Selenium
                selectors = ['.poster-container', '.film-poster']
                for selector in selectors:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for container in containers:
                        try:
                            if selector == '.film-poster':
                                parent = container.find_element(By.XPATH, "ancestor::a[1]")
                                img = container.find_element(By.TAG_NAME, 'img')
                                link = parent
                            else:
                                link = container.find_element(By.TAG_NAME, 'a')
                                img = container.find_element(By.TAG_NAME, 'img')
                            
                            films.append({
                                'title': img.get_attribute('alt'),
                                'poster': img.get_attribute('src'),
                                'url': link.get_attribute('href')
                            })
                        except Exception as e:
                            print(f"Erreur lors de l'extraction d'un film: {str(e)}")
                            continue
            else:
                films = films_data
            
            # Filtrer les entrées invalides et dédoublonner par titre
            seen_titles = set()
            unique_films = []
            for film in films:
                if film.get('title') and film.get('url') and film['title'] not in seen_titles:
                    seen_titles.add(film['title'])
                    film['url'] = film['url'].replace(self.base_url, '')
                    unique_films.append(film)
            
            return unique_films
            
        except Exception as e:
            print(f"Erreur lors de l'extraction des films: {str(e)}")
            return []

    def _get_film_details(self, film_url):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.driver.get(film_url)
                time.sleep(3)
                
                # Récupérer les informations avec JavaScript
                details = self.driver.execute_script("""
                    return {
                        director: document.querySelector('.film-director') ? 
                                document.querySelector('.film-director').textContent.trim() : 'Non disponible',
                        rating: document.querySelector('.average-rating') ? 
                                document.querySelector('.average-rating').textContent.trim() : 'Non noté',
                        year: document.querySelector('.film-header-lockup h1.headline-1 .number') ? 
                              document.querySelector('.film-header-lockup h1.headline-1 .number').textContent.trim() : '',
                        synopsis: document.querySelector('.truncate') ? 
                                 document.querySelector('.truncate').textContent.trim() : 'Synopsis non disponible'
                    };
                """)
                
                return details
                
            except Exception as e:
                print(f"Tentative {attempt + 1} échouée: {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        'director': "Non disponible",
                        'rating': "Non noté",
                        'year': "",
                        'synopsis': "Synopsis non disponible"
                    }
                time.sleep(2)

    def get_films(self, url):
        try:
            print(f"Démarrage de la récupération des films depuis {url}")
            
            if not self._is_valid_letterboxd_list_url(url):
                raise Exception("URL invalide. Veuillez entrer une URL de liste Letterboxd valide (watchlist, liste personnalisée ou films).")
            
            self._check_internet_connection()
            self._setup_driver()
            
            try:
                print("Chargement de la page...")
                self.driver.get(url)
                time.sleep(5)  # Attente plus longue pour le chargement initial
            except WebDriverException as e:
                raise Exception(f"Impossible d'accéder à la page. Erreur: {str(e)}")
            
            print("Scroll de la page...")
            self._wait_and_scroll()
            
            print("Extraction des films...")
            films = self._extract_films_from_page()
            
            print(f"Nombre de films trouvés: {len(films)}")
            if not films:
                raise Exception("Aucun film n'a pu être trouvé. Veuillez vérifier que la liste est publique et contient des films.")

            print("Sélection d'un film au hasard...")
            chosen_film = random.choice(films)
            print(f"Film choisi: {chosen_film['title']}")
            
            film_url = urljoin(self.base_url, chosen_film['url'])
            print(f"Récupération des détails du film depuis {film_url}")
            
            film_details = self._get_film_details(film_url)
            
            return {
                'title': chosen_film['title'],
                'poster': chosen_film['poster'].replace('_tmb', '_med'),
                'url': film_url,
                'director': film_details['director'],
                'rating': film_details['rating'],
                'year': film_details['year'],
                'synopsis': film_details['synopsis']
            }
            
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des films: {str(e)}")
            
        finally:
            self._cleanup_driver() 