from flask import Flask, render_template, request, jsonify, Response
from letterboxd_scraper import LetterboxdScraper
from flask_wtf import CSRFProtect
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
csrf = CSRFProtect(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/random-movie', methods=['POST'])
def get_random_movie():
    try:
        # Récupération de l'URL depuis le JSON (pour API via fetch)
        data = request.get_json()
        url = data.get('url') if data else None
        
        # Fallback pour form-data
        if not url and request.form:
            url = request.form.get('url')
            
        if not url:
            return jsonify({'error': 'URL manquante'}), 400
            
        if 'letterboxd.com' not in url:
            return jsonify({'error': 'URL invalide. Veuillez entrer une URL Letterboxd valide.'}), 400
        
        scraper = LetterboxdScraper()
        film = scraper.get_films(url)
        
        if not film:
            return jsonify({'error': 'Aucun film trouvé dans cette watchlist.'}), 404
        
        return jsonify(film)
    
    except Exception as e:
        return jsonify({'error': f'Une erreur est survenue: {str(e)}'}), 500

@app.route('/proxy-image')
def proxy_image():
    """Proxy pour récupérer les images de Letterboxd."""
    try:
        image_url = request.args.get('url')
        if not image_url:
            return jsonify({'error': 'URL de l\'image manquante'}), 400

        # Récupérer l'image
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        # Retourner l'image avec les bons headers
        return Response(
            response.iter_content(chunk_size=1024),
            content_type=response.headers['Content-Type'],
            headers={
                'Cache-Control': 'public, max-age=31536000',
                'Access-Control-Allow-Origin': '*'
            }
        )
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la récupération de l\'image: {str(e)}'}), 500

# Pour les environnements de développement
if __name__ == '__main__':
    app.run(debug=True) 