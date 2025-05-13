from flask import Flask, render_template, request, jsonify
from letterboxd_scraper import LetterboxdScraper
from flask_wtf import CSRFProtect
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
csrf = CSRFProtect(app)

# Configuration des templates pour Vercel
app.template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/random-movie', methods=['POST'])
def get_random_movie():
    url = request.form.get('url')
    if not url or 'letterboxd.com' not in url:
        return jsonify({'error': 'URL invalide. Veuillez entrer une URL Letterboxd valide.'}), 400
    
    try:
        scraper = LetterboxdScraper()
        film = scraper.get_films(url)
        if not film:
            return jsonify({'error': 'Aucun film trouvé dans cette liste.'}), 404
        
        return jsonify(film)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500 