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
from urllib.parse import urljoin

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

    def _check_internet_connection(self):
        try:
            requests.get(self.base_url, timeout=5)
            return True
        except requests.RequestException:
            raise Exception("Impossible de se connecter à Letterboxd. Veuillez vérifier votre connexion internet.")
        
    def _setup_driver(self):
        if not self.driver:
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=self.options)
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
                document.querySelectorAll('.poster-container').forEach(container => {
                    const link = container.querySelector('a');
                    const img = container.querySelector('img');
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
                containers = self.driver.find_elements(By.CSS_SELECTOR, '.poster-container')
                for container in containers:
                    try:
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
            
            # Filtrer les entrées invalides
            films = [f for f in films if f.get('title') and f.get('url')]
            
            # Convertir les URLs en chemins relatifs
            for film in films:
                film['url'] = film['url'].replace(self.base_url, '')
            
            return films
            
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
                raise Exception("Aucun film n'a pu être trouvé. Veuillez vérifier que la watchlist est publique et contient des films.")

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