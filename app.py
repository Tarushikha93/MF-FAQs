"""
Flask backend API for the Mutual Fund Chatbot.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from chatbot import MutualFundChatbot
import os
import json
from datetime import datetime
import pytz

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # Enable CORS for frontend

# Initialize chatbot
chatbot = MutualFundChatbot()

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'answer': "Please provide a question.",
                'source_url': None,
                'error': None
            }), 400
        
        # Get answer from chatbot
        response = chatbot.answer_question(query)
        
        return jsonify({
            'answer': response['answer'],
            'source_url': response.get('source_url'),
            'error': None
        }), 200
        
    except Exception as e:
        return jsonify({
            'answer': None,
            'source_url': None,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200

@app.route('/api/last-refreshed', methods=['GET'])
def last_refreshed():
    """Get the timestamp of when the data was last refreshed in IST."""
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'fund_data.json')
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        last_refreshed = data.get('last_refreshed', None)
        last_refreshed_iso = data.get('last_refreshed_iso', None)
        
        # If no timestamp exists, return None (data not yet refreshed)
        if not last_refreshed:
            return jsonify({
                'last_refreshed': None,
                'last_refreshed_iso': None,
                'message': 'Data has not been refreshed yet'
            }), 200
        
        return jsonify({
            'last_refreshed': last_refreshed,
            'last_refreshed_iso': last_refreshed_iso
        }), 200
        
    except Exception as e:
        return jsonify({
            'last_refreshed': None,
            'last_refreshed_iso': None,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

