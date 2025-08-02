from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Backend API configuration
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')
API_BASE = f"{BACKEND_URL}/api/v1"

# Helper function to make API requests to FastAPI backend
def make_api_request(endpoint, method='GET', data=None, files=None):
    """Make requests to FastAPI backend"""
    try:
        url = f"{API_BASE}{endpoint}"
        
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            if files:
                response = requests.post(url, files=files, data=data)
            else:
                response = requests.post(url, json=data)
        elif method == 'PUT':
            response = requests.put(url, json=data)
        elif method == 'DELETE':
            response = requests.delete(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': f'API request failed with status {response.status_code}'}
    except requests.exceptions.RequestException as e:
        return {'error': f'Connection error: {str(e)}'}

@app.route('/')
def dashboard():
    """Main dashboard page"""
    # Get system status and basic stats
    status_data = make_api_request('/health')
    return render_template('dashboard.html', status=status_data)

@app.route('/upload')
def upload_page():
    """File upload page"""
    return render_template('upload.html')

@app.route('/logs')
def logs_page():
    """Log analysis page"""
    # Get list of uploaded files
    files_data = make_api_request('/database/files')
    return render_template('logs.html', files=files_data)

@app.route('/anomalies')
def anomalies_page():
    """Anomaly detection results page"""
    return render_template('anomalies.html')

@app.route('/chat')
def chat_page():
    """AI chat interface page"""
    return render_template('chat.html')

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """Proxy upload requests to FastAPI backend"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Forward to FastAPI backend
    files = {'file': (file.filename, file.stream, file.content_type)}
    result = make_api_request('/upload', method='POST', files=files)
    return jsonify(result)

@app.route('/api/status')
def api_status():
    """Get backend system status"""
    # Call the correct backend health endpoint
    try:
        url = f"{BACKEND_URL}/health"
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
        else:
            result = {'error': f'Backend returned status {response.status_code}'}
    except requests.exceptions.RequestException as e:
        result = {'error': f'Connection error: {str(e)}'}
    
    return jsonify(result)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=3000, debug=True)