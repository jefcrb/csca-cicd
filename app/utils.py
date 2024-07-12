import os
import pandas as pd
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

from .entsoe import get_entsoe_data


def normalize_column_name(name, rename_map):
    name = name.lower()  # Convert to lowercase
    name = re.sub(r'[\s\/]', '_', name)  # Replace spaces and slashes with underscores
    name = re.sub(r'[^a-z0-9_]', '', name)  # Remove any other special characters
    return rename_map.get(name, name)

rename_map = {
    'indexatieparameter_x_ax__by__cz__d': 'indexatieparameter_x',
    'indexatieparameter_y_ax__by__cz__d': 'indexatieparameter_y',
    'waarde_x__mwh__vreg_waarde': 'waarde_x_vreg',
    'waarde_x__mwh__laatst_gekende_waarde': 'waarde_x_laatst_gekende',
    'waarde_y__mwh__vreg_waarde': 'waarde_y_vreg',
    'waarde_y__mwh__laatst_gekende_waarde': 'waarde_y_laatst_gekende'
}

def fetch_data():
    load_dotenv()
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

# Function to transform the data to the desired structure
def transform_data(filtered_data):
    grouped_data = {}
    for row in filtered_data:
        productnaam_key = re.sub(r'[^a-z0-9_]', '', re.sub(r'\s+', '_', row['productnaam'].lower()))

        row["prices"] = set_prices(row)

        if productnaam_key not in grouped_data:
            grouped_data[productnaam_key] = {
                'name': row['productnaam'],
                'supplier': row['handelsnaam'],
                'prijsonderdelen': []
            }
        grouped_data[productnaam_key]['prijsonderdelen'].append(row)
    return grouped_data


def set_prices(data):
    today = datetime.utcnow().strftime('%Y%m%d0000')
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime('%Y%m%d0000')
    specific_date = datetime(2024, 7, 6, tzinfo=timezone(timedelta(hours=2)))

    prices = {}
    prices["prices_today"] = []

    if data["vast_variabel_dynamisch"] == "Dynamisch":
        for i in range(24):
            specific_time = specific_date.replace(hour=i, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:00:00%z')
            prices["prices_today"].append({
                "time": specific_time,
                "price": calculate_price(data, "dyn", time=specific_time)
                })

    if data["vast_variabel_dynamisch"] == "Variabel":
        for i in range(24):
            specific_time = specific_date.replace(hour=i, minute=0, second=0, microsecond=0)
            prices["prices_today"].append({
                "time": specific_time.strftime('%Y-%m-%dT%H:00:00%z'),
                "price": calculate_price(data, "var")
                })

    if data["vast_variabel_dynamisch"] == "Vast":
        for i in range(24):
            specific_time = specific_date.replace(hour=i, minute=0, second=0, microsecond=0)
            prices["prices_today"].append({
                "time": specific_time.strftime('%Y-%m-%dT%H:00:00%z'),
                "price": calculate_price(data, "vast")
                })
    

    return prices


def calculate_price(data, type, time=None):
    price = 0
    if type == "var":
        if data["prijs"]:
            price = data["prijs"]
        
        elif data["a"] and data["waarde_x_laatst_gekende"]:
            price = float(data["a"]) * float(data["waarde_x_laatst_gekende"]) + data["d"]
        
    if type == "vast":
        price = data["prijs"]
    
    if type == "dyn":
        if data["prijs"]:
            price = data["prijs"]
        
        if data["a"] and data["d"]:
            entsoe_data = get_entsoe_data()
            for row in entsoe_data:
                if row["start"] == time:
                    price = float(data["a"]) * float(row["price"]) + data["d"]
    
    if data["contracttype"] == "Afname" and data["energietype"] == "Elektriciteit":
        price += data["groene_stroom"] + data["wkk"]

    return price