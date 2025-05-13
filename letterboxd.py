from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
from rich import print
import time

# Config
url = "https://letterboxd.com/Maggra/watchlist/"
options = Options()
options.add_argument("--headless")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")

def get_films(driver):
    try:
        # Attendre que la page soit chargée
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "poster-list"))
        )
        
        # Solution 1: Plus fiable avec JavaScript
        films = driver.execute_script("""
            return Array.from(document.querySelectorAll('li.poster-container img'))
                   .map(img => img.alt);
        """)
        
        # Solution alternative si JS ne fonctionne pas
        if not films:
            films = [img.get_attribute("alt") for img in driver.find_elements(
                By.CSS_SELECTOR, "li.poster-container img"
            )]
        
        return films
        
    except Exception as e:
        print(f"⚠️ Erreur: {e}")
        return None

# Main
try:
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.get(url)
    
    # Scroll pour charger toutes les images (important pour le lazy loading)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Laisse le temps au lazy loading
    
    films = get_films(driver)
    
    if films:
        print("✨ Roulette Letterboxd en cours...", end="", flush=True)
        for _ in range(5):
            time.sleep(0.3)
            print(".", end="", flush=True)
        print(f"[bold green]🎬 Film choisi :[/bold green] [cyan]{random.choice(films)}[/cyan]")
    else:
        print("❌ Aucun film trouvé. Essayez ces vérifications :")
        print("- La watchlist n'est pas vide")
        print("- L'URL est correcte")
        print("- Essayez sans mode headless pour debugger")

finally:
    driver.quit()
