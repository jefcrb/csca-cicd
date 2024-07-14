from flask import request, jsonify, send_from_directory, abort
from functools import wraps
from .utils import transform_data
from . import db
from .models import Data
from .entsoe import get_entsoe_data
import os

SECURITY_TOKEN = os.getenv('SECURE_TOKEN')

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token != SECURITY_TOKEN:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def init_routes(app):
    @app.route('/')
    @token_required
    def serve_index():
        return send_from_directory('../templates', 'index.html')

    @app.route('/data', methods=['GET'])
    @token_required
    def get_data():
        filters = {
            'jaar': request.args.get('jaar'),
            'maand': request.args.get('maand'),
            'segment': request.args.get('segment'),
            'energietype': request.args.get('energietype'),
            'handelsnaam': request.args.get('handelsnaam')
        }

        query = Data.query
        for key, value in filters.items():
            if value:
                query = query.filter(getattr(Data, key).ilike(f'%{value}%'))

        result = query.all()
        result_dict = [row.to_dict() for row in result]
        transformed_data = transform_data(result_dict)

        return jsonify(transformed_data)
