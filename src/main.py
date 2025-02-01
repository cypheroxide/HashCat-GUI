#!/usr/bin/env python3
"""
Main entry point for HashCat-GUI application.
Handles web server setup and WebSocket integration.
"""
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import os
from core.config import Config
from core.hashcat import HashcatRunner

app = Flask(__name__, 
        template_folder="gui/templates",
        static_folder="gui/static")
socketio = SocketIO(app)
config = Config()
hashcat = HashcatRunner(config)

@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@app.route('/api/wordlists')
def get_wordlists():
    """Get available wordlists"""
    wordlists_path = config.get_path('wordlists')
    wordlists = []
    if wordlists_path.exists():
        wordlists = [f.name for f in wordlists_path.glob('**/*') if f.is_file()]
    return jsonify(wordlists)

@app.route('/api/rules')
def get_rules():
    """Get available hashcat rules"""
    rules_path = config.get_path('rules')
    rules = []
    if rules_path.exists():
        rules = [f.name for f in rules_path.glob('*.rule') if f.is_file()]
    return jsonify(rules)

@app.route('/api/verify')
def verify_setup():
    """Verify system setup and requirements"""
    paths = config.verify_paths()
    binaries = config.verify_binaries()
    return jsonify({
        'paths': paths,
        'binaries': binaries
    })

@socketio.on('start_crack')
def handle_crack_start(data):
    """Handle password cracking job start"""
    try:
        job_id = hashcat.start_crack(
            hash_type=data['hash_type'],
            hash_value=data['hash'],
            wordlist=data['wordlist'],
            rule=data.get('rule'),
            attack_mode=data.get('attack_mode', 0)
        )
        emit('job_started', {'job_id': job_id})
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('stop_crack')
def handle_crack_stop(data):
    """Handle stopping a running crack job"""
    try:
        hashcat.stop_crack(data['job_id'])
        emit('job_stopped', {'job_id': data['job_id']})
    except Exception as e:
        emit('error', {'message': str(e)})

def run_server(debug=False, host='127.0.0.1', port=5000):
    """Run the Flask application server"""
    socketio.run(app, host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_server(debug=True)

