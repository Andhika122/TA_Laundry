"""
API Module - REST API
"""
from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__)


@api_bp.route('/status')
def status():
    """API status"""
    return jsonify({'status': 'ok', 'message': 'API is running'})
