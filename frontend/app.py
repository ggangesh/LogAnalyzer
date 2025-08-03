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

@app.route('/insights')
def insights_page():
    """AI insights and summaries page"""
    return render_template('insights.html')

@app.route('/charts')
def charts_page():
    """Data visualization and charts page"""
    return render_template('charts.html')

@app.route('/reports')
def reports_page():
    """Reports generation and download page"""
    return render_template('reports.html')

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

# JSON Report Download Routes
@app.route('/api/reports/download/basic/<file_id>')
def download_basic_report(file_id):
    """Download basic JSON report"""
    try:
        url = f"{API_BASE}/reports/download/basic/{file_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            # Return the JSON response with proper headers for download
            from flask import Response
            return Response(
                response.content,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=logsage_basic_report_{file_id}.json'
                }
            )
        else:
            return jsonify({'error': f'Failed to generate report: {response.status_code}'}), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 500

@app.route('/api/reports/download/detailed/<file_id>')
def download_detailed_report(file_id):
    """Download detailed JSON report"""
    try:
        include_anomalies = request.args.get('include_anomalies', 'true').lower() == 'true'
        include_summary = request.args.get('include_summary', 'true').lower() == 'true'
        
        url = f"{API_BASE}/reports/download/detailed/{file_id}"
        params = {
            'include_anomalies': include_anomalies,
            'include_summary': include_summary
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            from flask import Response
            return Response(
                response.content,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=logsage_detailed_report_{file_id}.json'
                }
            )
        else:
            return jsonify({'error': f'Failed to generate report: {response.status_code}'}), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 500

@app.route('/api/reports/download/filtered/<file_id>', methods=['POST'])
def download_filtered_report(file_id):
    """Download filtered JSON report"""
    try:
        filter_data = request.get_json() or {}
        
        url = f"{API_BASE}/reports/download/filtered/{file_id}"
        response = requests.post(url, json=filter_data)
        
        if response.status_code == 200:
            from flask import Response
            return Response(
                response.content,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=logsage_filtered_report_{file_id}.json'
                }
            )
        else:
            return jsonify({'error': f'Failed to generate report: {response.status_code}'}), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 500

@app.route('/api/reports/generate/basic/<file_id>')
def generate_basic_report(file_id):
    """Generate basic JSON report"""
    try:
        url = f"{API_BASE}/reports/basic/{file_id}"
        response = requests.post(url)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'Failed to generate report: {response.status_code}'}), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 500

@app.route('/api/reports/generate/detailed/<file_id>')
def generate_detailed_report(file_id):
    """Generate detailed JSON report"""
    try:
        include_anomalies = request.args.get('include_anomalies', 'true').lower() == 'true'
        include_summary = request.args.get('include_summary', 'true').lower() == 'true'
        
        url = f"{API_BASE}/reports/detailed/{file_id}"
        params = {
            'include_anomalies': include_anomalies,
            'include_summary': include_summary
        }
        response = requests.post(url, params=params)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'Failed to generate report: {response.status_code}'}), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 500

@app.route('/api/reports/preview/<file_id>')
def preview_report(file_id):
    """Preview report data"""
    try:
        report_type = request.args.get('report_type', 'basic')
        limit = request.args.get('limit', '10')
        
        url = f"{API_BASE}/reports/preview/{file_id}"
        params = {
            'report_type': report_type,
            'limit': limit
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'Failed to preview report: {response.status_code}'}), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 500

@app.route('/api/reports/types')
def get_report_types():
    """Get available report types"""
    try:
        url = f"{API_BASE}/reports/types"
        response = requests.get(url)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'Failed to get report types: {response.status_code}'}), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=3000, debug=True)