import os
import pandas as pd
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

from .entsoe import get_entsoe_data


BIJZ_ACCIJNS = 1.4121
BIJDRAGE_ENERGIE = 0.1926
AANSLUITINGSVERGOEDING = 0.075
AFNAME_REGIO = 4.33

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


def transform_data(filtered_data, show_prices = False):
    grouped_data = {}
    for row in filtered_data:
        productnaam_key = re.sub(r'[^a-z0-9_]', '', re.sub(r'\s+', '_', row['productnaam'].lower()))

        if show_prices:
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
    today = datetime.now().strftime('%Y%m%d0000')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d0000')
    specific_date = datetime.now().replace(tzinfo=timezone(timedelta(hours=2)))

    prices = {}
    prices["prices_today"] = []
    prices["prices_tomorrow"] = []
    prices["prices_next24h"] = []

    if data["vast_variabel_dynamisch"] == "Dynamisch":
        for i in range(24):
            specific_time = specific_date.replace(hour=i, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:00:00%z')
            prices_today = calculate_price(data, "dyn", time=specific_time)
            prices["prices_today"].append({
                "time": specific_time,
                "price": prices_today
                })

            specific_time_tomorrow = (specific_date + timedelta(days=1)).replace(hour=i, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:00:00%z')
            prices_tomorrow = calculate_price(data, "dyn", time=specific_time_tomorrow) if datetime.now().hour >= 12 else 0
            prices["prices_tomorrow"].append({
                "time": specific_time_tomorrow,
                "price": prices_tomorrow
                })

    if data["vast_variabel_dynamisch"] == "Variabel":
        for i in range(24):
            specific_time = specific_date.replace(hour=i, minute=0, second=0, microsecond=0)
            prices_today = calculate_price(data, "var")
            prices["prices_today"].append({
                "time": specific_time.strftime('%Y-%m-%dT%H:00:00%z'),
                "price": prices_today
                })

            specific_time_tomorrow = (specific_date + timedelta(days=1)).replace(hour=i, minute=0, second=0, microsecond=0)
            prices_tomorrow = calculate_price(data, "var") if datetime.now().hour >= 12 else 0
            prices["prices_tomorrow"].append({
                "time": specific_time_tomorrow.strftime('%Y-%m-%dT%H:00:00%z'),
                "price": prices_tomorrow
                })

    if data["vast_variabel_dynamisch"] == "Vast":
        for i in range(24):
            specific_time = specific_date.replace(hour=i, minute=0, second=0, microsecond=0)
            prices_today = calculate_price(data, "vast")
            prices["prices_today"].append({
                "time": specific_time.strftime('%Y-%m-%dT%H:00:00%z'),
                "price": prices_today
                })

            specific_time_tomorrow = (specific_date + timedelta(days=1)).replace(hour=i, minute=0, second=0, microsecond=0)
            prices_tomorrow = calculate_price(data, "vast") if datetime.now().hour >= 12 else 0
            prices["prices_tomorrow"].append({
                "time": specific_time_tomorrow.strftime('%Y-%m-%dT%H:00:00%z'),
                "price": prices_tomorrow
                })
    
    current_hour = specific_date.hour

    for i in range(24):
        if i + current_hour < 24:
            specific_time_next24h = specific_date.replace(hour=(i + current_hour) % 24, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:00:00%z')
            prices_next24h = prices["prices_today"][(i + current_hour) % 24]["price"]
        else:
            specific_time_next24h = (specific_date + timedelta(days=1)).replace(hour=(i + current_hour) % 24, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:00:00%z')
            prices_next24h = prices["prices_tomorrow"][(i + current_hour) % 24]["price"]
        prices["prices_next24h"].append({
            "time": specific_time_next24h,
            "price": prices_next24h
        })

    prices["today_min"] = min(p["price"] for p in prices["prices_today"])
    prices["today_max"] = max(p["price"] for p in prices["prices_today"])
    prices["today_avg"] = sum(p["price"] for p in prices["prices_today"]) / len(prices["prices_today"])

    prices["tomorrow_min"] = min(p["price"] for p in prices["prices_tomorrow"])
    prices["tomorrow_max"] = max(p["price"] for p in prices["prices_tomorrow"])
    prices["tomorrow_avg"] = sum(p["price"] for p in prices["prices_tomorrow"]) / len(prices["prices_tomorrow"])

    prices["next24h_min"] = min(p["price"] for p in prices["prices_next24h"])
    prices["next24h_max"] = max(p["price"] for p in prices["prices_next24h"])
    prices["next24h_avg"] = sum(p["price"] for p in prices["prices_next24h"]) / len(prices["prices_next24h"])

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
                    # print(f'{data["productnaam"]} {data["contracttype"]}: {float(data["a"])} * {float(row["price"])} + {data["d"]} = {price}')
    
    if data["contracttype"] == "Afname" and data["energietype"] == "Elektriciteit":
        price *= 1.06
        price += data["groene_stroom"] + data["wkk"] + BIJZ_ACCIJNS + BIJDRAGE_ENERGIE + AANSLUITINGSVERGOEDING + AFNAME_REGIO

    price = round(price, 6)
    return price
