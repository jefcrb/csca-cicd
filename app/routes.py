from flask import request, jsonify, send_from_directory, abort
from functools import wraps
from .utils import transform_data
from . import db
from .models import Data
from .entsoe import get_entsoe_data
from .netkosten import get_cost_from_zip
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
    # @token_required
    def serve_index():
        return send_from_directory('../templates', 'index.html')

    @app.route('/data', methods=['GET'])
    # @token_required
    def get_data():
        filters = {
            'jaar': request.args.get('jaar'),
            'maand': request.args.get('maand'),
            'segment': request.args.get('segment'),
            'energietype': request.args.get('energietype'),
            'handelsnaam': request.args.get('handelsnaam'),
            'contracttype': request.args.get('contracttype'),
            'vast_variabel_dynamisch': request.args.get('vast_variabel_dynamisch')
        }

        show_prices = request.args.get('show_prices')
        top = request.args.get('top', type=int)
        bottom = request.args.get('bottom', type=int)
        postcode = request.args.get('postcode')

        afname_regio = get_cost_from_zip(postcode)

        query = Data.query
        for key, value in filters.items():
            if value:
                query = query.filter(getattr(Data, key).ilike(f'%{value}%'))

        result = query.all()
        result_dict = [row.to_dict() for row in result]
        transformed_data = transform_data(result_dict, show_prices=show_prices, afname_regio_val=afname_regio)

        all_entries = []
        for key, value in transformed_data.items():
            for entry in value['prijsonderdelen']:
                entry['type'] = key
                all_entries.append(entry)

        if top is not None:
            all_entries.sort(key=lambda x: x['prices']['today_avg'], reverse=True)
            all_entries = all_entries[:top]

        if bottom is not None:
            all_entries.sort(key=lambda x: x['prices']['today_avg'])
            all_entries = all_entries[:bottom]

        filtered_data = {}
        for entry in all_entries:
            type_key = entry.pop('type')
            if type_key not in filtered_data:
                filtered_data[type_key] = {
                    'name': transformed_data[type_key]['name'],
                    'prijsonderdelen': []
                }
            filtered_data[type_key]['prijsonderdelen'].append(entry)

        return jsonify(filtered_data)
