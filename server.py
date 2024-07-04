import os
import pandas as pd
import re
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory

# Load environment variables from .env file
load_dotenv()

# Function to normalize column names
def normalize_column_name(name, rename_map):
    name = name.lower()  # Convert to lowercase
    name = re.sub(r'[\s\/]', '_', name)  # Replace spaces and slashes with underscores
    name = re.sub(r'[^a-z0-9_]', '', name)  # Remove any other special characters
    return rename_map.get(name, name)

# Dictionary to map original column names to desired normalized names
rename_map = {
    'indexatieparameter_x_ax__by__cz__d': 'indexatieparameter_x',
    'indexatieparameter_y_ax__by__cz__d': 'indexatieparameter_y',
    'waarde_x__mwh__vreg_waarde': 'waarde_x_vreg',
    'waarde_x__mwh__laatst_gekende_waarde': 'waarde_x_laatst_gekende',
    'waarde_y__mwh__vreg_waarde': 'waarde_y_vreg',
    'waarde_y__mwh__laatst_gekende_waarde': 'waarde_y_laatst_gekende'
}

# Initialize Flask app
app = Flask(__name__)

# Function to fetch and preprocess data
def fetch_data():
    src_url = os.getenv('SRC_URL')
    if src_url:
        try:
            # Read the second and third sheets of the Excel file from the URL
            data_sheet_2 = pd.read_excel(src_url, sheet_name=1)
            data_sheet_3 = pd.read_excel(src_url, sheet_name=2)

            # Normalize the column names
            data_sheet_2.columns = [normalize_column_name(col, rename_map) for col in data_sheet_2.columns]
            data_sheet_3.columns = [normalize_column_name(col, rename_map) for col in data_sheet_3.columns]

            # Append the data from the third sheet to the second sheet
            combined_data = pd.concat([data_sheet_2, data_sheet_3], ignore_index=True)

            return combined_data
        except Exception as e:
            print(f"An error occurred: {e}")
            return pd.DataFrame()
    else:
        print("SRC_URL is not set in the .env file.")
        return pd.DataFrame()

# Load data on server startup
data = fetch_data()

# Route to serve the index.html file
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Route to handle filtered data requests
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

    filtered_data = data.copy()
    for key, value in filters.items():
        if value:
            filtered_data = filtered_data[filtered_data[key].astype(str).str.lower() == value.lower()]

    return jsonify(filtered_data.to_dict(orient='records'))

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
