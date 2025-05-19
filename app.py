from flask import Flask, render_template, request, jsonify, Response, send_file
from letterboxd_scraper import LetterboxdScraper
from flask_wtf import CSRFProtect
import os
import requests
from io import BytesIO

app = Flask(__name__)
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
        if list_type == 'watchlist':
            url = f'https://letterboxd.com/{username}/watchlist/'
        elif list_type == 'list':
            url = f'https://letterboxd.com/list/{username}/'
        elif list_type == 'films':
            url = f'https://letterboxd.com/{username}/films/'
        else:
            return jsonify({'error': 'Type de liste invalide'}), 400
        
        scraper = LetterboxdScraper()
        film = scraper.get_films(url)
        
        if not film:
            return jsonify({'error': 'Aucun film trouvé dans cette liste.'}), 404
        
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

        # Créer un objet BytesIO pour stocker l'image
        img_io = BytesIO(response.content)
        img_io.seek(0)

        # Retourner l'image avec les bons headers
        return send_file(
            img_io,
            mimetype=response.headers['Content-Type'],
            as_attachment=False,
            download_name='poster.jpg'
        )
    except Exception as e:
        print(f"Erreur proxy-image: {str(e)}")
        return jsonify({'error': f'Erreur lors de la récupération de l\'image: {str(e)}'}), 500

# Pour les environnements de développement
if __name__ == '__main__':
    app.run(debug=True) 