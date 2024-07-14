from flask import request, jsonify, send_from_directory
from .utils import transform_data
from . import db
from .models import Data
from .entsoe import get_entsoe_data
from sqlalchemy import and_

def init_routes(app):
    @app.route('/')
    def serve_index():
        return send_from_directory('../templates', 'index.html')

    @app.route('/data', methods=['GET'])
    def get_data():
        filters = {
            'jaar': request.args.get('jaar'),
            'maand': request.args.get('maand'),
            'segment': request.args.get('segment'),
            'energietype': request.args.get('energietype')
        }

        query = Data.query
        for key, value in filters.items():
            if value:
                query = query.filter(getattr(Data, key).ilike(f'%{value}%'))

        result = query.all()
        result_dict = [row.to_dict() for row in result]
        transformed_data = transform_data(result_dict)

        return jsonify(transformed_data)

    @app.route('/entsoe_data', methods=['GET'])
    def get_entsoe():
        data = get_entsoe_data()
        return jsonify(data)
