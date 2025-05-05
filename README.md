# 🎬 Roulette Letterboxd

**Un script Python pour découvrir un film aléatoire dans ta watchlist Letterboxd**  
*(Parfait pour les indécis·es !)*

## 📦 Fonctionnalités
- ✔️ Tire un film aléatoire dans ta watchlist
- ✔️ Compatible Windows/MacOS/Linux

## 🚀 Installation

### 1. Cloner le dépôt
```bash
git clone https://github.com/ton_user/roulette_letterboxd.git
cd roulette_letterboxd
```

### 2. Créer un environnement virtuel (recommandé)
**Linux/Mac :**
```bash
python -m venv venv_letterboxd
source venv_letterboxd/bin/activate
```

**Windows :**
```cmd
python -m venv venv_letterboxd
venv_letterboxd\Scripts\activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Lancer le script
```bash
python letterboxd.py
```

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

