from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import random
from rich import print
import time


#url a changer en fonction du User
url = "https://letterboxd.com/Maggra/watchlist/"


options = Options()
options.add_argument("--headless")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(url)

# Récupération des films avec le bon sélecteur
films = [img.get_attribute("alt") for img in driver.find_elements("css selector", "li.poster-container img")]
driver.quit()

if films:
    print("✨ Roulette Letterboxd en cours...", end="", flush=True)
    for _ in range(5):
        time.sleep(0.3)
        print(".", end="", flush=True)
    print(f"[bold green]🎬 Film choisi :[/bold green] [cyan]{random.choice(films)}[/cyan]")
else:
    print("❌ Aucun film trouvé. Essaye ce sélecteur alternatif :")
    print('driver.find_elements("css selector", "div.film-poster img")')
