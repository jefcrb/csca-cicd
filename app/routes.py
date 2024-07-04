from flask import request, jsonify, send_from_directory, current_app
from .utils import transform_data

def init_routes(app):
    @app.route('/')
    def serve_index():
        return send_from_directory('templates', 'index.html')

    @app.route('/data', methods=['GET'])
    def get_data():
        filters = {
            'jaar': request.args.get('year'),
            'maand': request.args.get('month'),
            'segment': request.args.get('segment'),
            'energietype': request.args.get('energytype'),
            'handelsnaam': request.args.get('supplier'),
            'vast_variabel_dynamisch': request.args.get('type')
        }

        filtered_data = current_app.data.copy()
        for key, value in filters.items():
            if value:
                filtered_data = filtered_data[filtered_data[key].astype(str).str.lower() == value.lower()]

        transformed_data = transform_data(filtered_data)

        return jsonify(transformed_data)
