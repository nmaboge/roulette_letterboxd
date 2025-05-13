# 🎬 Roulette Letterboxd

Une application web qui permet de choisir aléatoirement un film dans votre watchlist Letterboxd.

## 🚀 Installation

1. Clonez ce dépôt :
```bash
git clone https://github.com/votre-username/roulette-letterboxd.git
cd roulette-letterboxd
```

2. Créez un environnement virtuel Python et activez-le :
```bash
python -m venv venv
source venv/bin/activate  # Sur Unix/MacOS
# ou
venv\Scripts\activate  # Sur Windows
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## 🎯 Utilisation

1. Lancez l'application :
```bash
python app.py
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
remplacer l'url par l'url de la liste ou watchlist voulu
```

## 📸 Exemple de sortie
```
🎲 Film sélectionné : "Parasite"
```

