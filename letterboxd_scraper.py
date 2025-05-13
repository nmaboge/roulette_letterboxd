from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

class LetterboxdScraper:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        self.driver = None

    def _setup_driver(self):
        if not self.driver:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.options
            )

    def _cleanup_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def get_films(self, url):
        try:
            self._setup_driver()
            self.driver.get(url)
            
            # Scroll pour charger toutes les images
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Attente pour le lazy loading
            
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "poster-list"))
            )
            
            # Récupérer les films avec JavaScript
            films = self.driver.execute_script("""
                return Array.from(document.querySelectorAll('li.poster-container img'))
                       .map(img => img.alt);
            """)
            
            # Solution alternative si JS ne fonctionne pas
            if not films:
                films = [img.get_attribute("alt") for img in self.driver.find_elements(
                    By.CSS_SELECTOR, "li.poster-container img"
                )]
            
            return films
            
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des films: {str(e)}")
            
        finally:
            self._cleanup_driver() 