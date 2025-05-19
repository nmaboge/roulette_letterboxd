from flask import Flask, render_template, request, jsonify
from .letterboxd_scraper import LetterboxdScraper
from flask_wtf import CSRFProtect
import os
import requests

app = Flask(__name__, 
    static_folder=os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')),
    template_folder=os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
csrf = CSRFProtect(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/random-movie', methods=['POST'])
def get_random_movie():
    try:
        # Récupération des données depuis le JSON
        data = request.get_json()
        list_type = data.get('type')
        username = data.get('username')
        
        # Fallback pour form-data
        if not list_type and request.form:
            list_type = request.form.get('type')
            username = request.form.get('username')
            
        if not list_type or not username:
            return jsonify({'error': 'Type de liste et pseudo requis'}), 400
            
        # Construction de l'URL selon le type
        try:
            if list_type == 'watchlist':
                url = f'https://letterboxd.com/{username}/watchlist/'
            elif list_type == 'list':
                # Pour les listes personnalisées, le username est en fait le nom de la liste
                url = f'https://letterboxd.com/list/{username}/'
            elif list_type == 'films':
                url = f'https://letterboxd.com/{username}/films/'
            else:
                return jsonify({'error': 'Type de liste invalide'}), 400
        except Exception as e:
            return jsonify({'error': f'Erreur lors de la construction de l\'URL: {str(e)}'}), 400
        
        try:
            scraper = LetterboxdScraper()
            film = scraper.get_films(url)
            
            if not film:
                return jsonify({'error': 'Aucun film trouvé dans cette liste.'}), 404
            
            return jsonify(film)
        except requests.exceptions.RequestException as e:
            return jsonify({'error': 'Impossible d\'accéder à la liste. Vérifiez que le pseudo ou le nom de la liste est correct.'}), 404
        except Exception as e:
            return jsonify({'error': f'Erreur lors de la récupération des films: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Une erreur est survenue: {str(e)}'}), 500

# Pour le développement local
if __name__ == '__main__':
    app.run(debug=True) 