from flask import Flask, render_template, request, jsonify
from letterboxd_scraper import LetterboxdScraper
from flask_wtf import CSRFProtect
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
csrf = CSRFProtect(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_random_movie', methods=['POST'])
def get_random_movie():
    url = request.form.get('url')
    if not url or 'letterboxd.com' not in url or 'watchlist' not in url:
        return jsonify({'error': 'URL invalide. Veuillez entrer une URL de watchlist Letterboxd valide.'}), 400
    
    try:
        scraper = LetterboxdScraper()
        films = scraper.get_films(url)
        if not films:
            return jsonify({'error': 'Aucun film trouvé dans cette watchlist.'}), 404
        
        import random
        chosen_film = random.choice(films)
        return jsonify({'film': chosen_film})
    
    except Exception as e:
        return jsonify({'error': f'Une erreur est survenue: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True) 