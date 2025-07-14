# Roulette Letterboxd

Une application web qui sélectionne aléatoirement un film depuis une liste Letterboxd.

## Fonctionnalités

- Support des watchlists Letterboxd
- Support des listes personnalisées
- Support des pages de films d'utilisateur
- Interface moderne et responsive
- Affichage des détails du film (réalisateur, année, note, synopsis)

## Déploiement sur Vercel

1. Créez un compte sur [Vercel](https://vercel.com/signup) si ce n'est pas déjà fait
2. Allez sur [https://vercel.com/new](https://vercel.com/new)
3. Importez ce projet depuis GitHub
4. Dans les paramètres du projet, ajoutez les variables d'environnement suivantes :
   - `FLASK_ENV`: `production`
   - `PYTHONPATH`: `/var/task`
   - `CHROME_PATH`: `/opt/google/chrome/chrome`
5. Déployez !

## Développement local

1. Créez un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sur Unix
# ou
venv\Scripts\activate  # Sur Windows
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Lancez l'application :
```bash
python api/index.py
```

## Structure du projet

- `api/` : Code de l'application Flask et du scraper
  - `index.py` : Point d'entrée de l'application
  - `letterboxd_scraper.py` : Logique de scraping
- `templates/` : Templates HTML
- `vercel.json` : Configuration du déploiement
- `requirements.txt` : Dépendances Python

## 🎯 Utilisation

1. Lancez l'application :
```bash
python api/index.py
```

2. Ouvrez votre navigateur et accédez à `http://localhost:5000`

3. Collez l'URL de votre watchlist Letterboxd (par exemple : `https://letterboxd.com/username/watchlist/`)

4. Cliquez sur le bouton pour obtenir un film aléatoire !

## 🛠 Fonctionnalités

- Interface web moderne et responsive
- Sélection aléatoire dans votre watchlist Letterboxd
- Gestion des erreurs et retours utilisateur
- Mode headless (pas de fenêtre de navigateur visible)

## 📝 Notes

- L'application nécessite Chrome/Chromium d'installé sur votre système
- La watchlist Letterboxd doit être publique
- Le temps de chargement peut varier selon la taille de votre watchlist

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📦 Fonctionnalités
- ✔️ Tire un film aléatoire dans ta watchlist
- ✔️ Compatible Windows/MacOS/Linux

## ⚙️ Configuration
Créez un fichier `config.ini` :
```ini
[letterboxd]
Remplacez l’URL par l’URL de la liste ou watchlist voulue
```

## 📸 Exemple de sortie
```
🎲 Film sélectionné : "Parasite"
```

