"""
server.py
Flask web server for Keystone Growth Partners.
Serves index.html and handles API routes for lead capture and contact forms.

Run with: python server.py
Site will be live at http://localhost:5000
"""

import os
import re
import logging
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

from tools.db import init_db, insert_subscriber, insert_contact
from tools.email_notifier import notify_new_subscriber, notify_new_contact

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-in-production')

CALENDLY_URL = os.getenv('CALENDLY_URL', '')
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip()))


def get_client_ip() -> str:
    return request.headers.get('X-Forwarded-For', request.remote_addr)


# ── Page Routes ────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static'), filename)


# ── API Routes ─────────────────────────────────────────────────────────────────

@app.route('/api/subscribe', methods=['POST'])
def api_subscribe():
    """
    Handle CTA email capture form.
    Body: {"email": "user@example.com"}
    Returns 200/400/409/500
    """
    data = request.get_json(silent=True)
    if not data or 'email' not in data:
        return jsonify({'status': 'error', 'message': 'Email is required.'}), 400

    email = data['email'].strip()
    if not is_valid_email(email):
        return jsonify({'status': 'error', 'message': 'Please enter a valid email address.'}), 400

    ip     = get_client_ip()
    result = insert_subscriber(email, ip_address=ip, source='cta_form')

    if result['success']:
        notify_new_subscriber(email, ip_address=ip)
        logger.info(f'New subscriber: {email}')
        return jsonify({'status': 'ok', 'message': "You're on the list. We'll be in touch."}), 200
    elif result.get('error') == 'already_subscribed':
        return jsonify({'status': 'already_subscribed', 'message': "You're already on the list."}), 409
    else:
        logger.error(f'DB error on subscribe: {result.get("error")}')
        return jsonify({'status': 'error', 'message': 'Something went wrong. Please try again.'}), 500


@app.route('/api/contact', methods=['POST'])
def api_contact():
    """
    Handle contact modal form submissions.
    Body: {"name": "...", "email": "...", "message": "..."}
    Returns 200/400/500
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid request.'}), 400

    name    = data.get('name', '').strip()
    email   = data.get('email', '').strip()
    message = data.get('message', '').strip()

    errors = []
    if not name:
        errors.append('Name is required.')
    if not email or not is_valid_email(email):
        errors.append('A valid email address is required.')
    if not message or len(message) < 10:
        errors.append('Message must be at least 10 characters.')
    if len(message) > 2000:
        errors.append('Message must be under 2000 characters.')

    if errors:
        return jsonify({'status': 'error', 'message': ' '.join(errors)}), 400

    ip     = get_client_ip()
    result = insert_contact(name, email, message, ip_address=ip)

    if result['success']:
        notify_new_contact(name, email, message, ip_address=ip)
        logger.info(f'New contact from: {name} <{email}>')
        return jsonify({'status': 'ok', 'message': "Message received. We'll be in touch within 24 hours."}), 200
    else:
        logger.error(f'DB error on contact: {result.get("error")}')
        return jsonify({'status': 'error', 'message': 'Something went wrong. Please try again.'}), 500


@app.route('/api/calendly-url', methods=['GET'])
def api_calendly_url():
    """
    Return the Calendly URL from .env so it never needs to be hardcoded in HTML.
    """
    if CALENDLY_URL:
        return jsonify({'url': CALENDLY_URL}), 200
    return jsonify({'url': None, 'message': 'Booking URL not configured'}), 503


# ── Startup ────────────────────────────────────────────────────────────────────

init_db()

if __name__ == '__main__':
    port  = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    logger.info(f'Keystone Growth Partners server starting → http://localhost:{port}')
    app.run(host='0.0.0.0', port=port, debug=debug)
