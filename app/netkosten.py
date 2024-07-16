import requests
import pandas as pd
from io import BytesIO

REGIONS_URLS_AFNAME = [
    {"Fluvius Antwerpen": "https://www.fluvius.be/sites/fluvius/files/2023-12/distributienettarieven-elektriciteit-afname-fluvius-antwerpen-01012024-31122024.xlsx"},
    {"Fluvius Limburg": "https://www.fluvius.be/sites/fluvius/files/2023-12/distributienettarieven-elektriciteit-afname-fluvius-limburg-01012024-31122024.xlsx"},
    {"Fluvius West": "https://www.fluvius.be/sites/fluvius/files/2023-12/distributienettarieven-elektriciteit-afname-fluvius-west-01012024-31122024.xlsx"},
    {"Gaselwest": "https://www.fluvius.be/sites/fluvius/files/2023-12/distributienettarieven-elektriciteit-afname-gaselwest-01012024-31122024.xlsx"},
    {"Imewo": "https://www.fluvius.be/sites/fluvius/files/2023-12/distributienettarieven-elektriciteit-afname-imewo-01012024-31122024.xlsx"},
    {"Intergem": "https://www.fluvius.be/sites/fluvius/files/2023-12/distributienettarieven-elektriciteit-afname-intergem-01012024-31122024.xlsx"},
    {"Iveka": "https://www.fluvius.be/sites/fluvius/files/2023-12/distributienettarieven-elektriciteit-afname-iveka-01012024-31122024.xlsx"},
    {"Iverlek": "https://www.fluvius.be/sites/fluvius/files/2023-12/distributienettarieven-elektriciteit-afname-iverlek-01012024-31122024.xlsx"},
    {"Pbe": "https://www.fluvius.be/sites/fluvius/files/2023-12/distributienettarieven-elektriciteit-afname-pbe-01012024-31122024.xlsx"},
    {"Sibelgas": "https://www.fluvius.be/sites/fluvius/files/2023-12/distributienettarieven-elektriciteit-afname-sibelgas-01012024-31122024.xlsx"}
]

ZIPCODE_DATA_URL = "https://opendata.fluvius.be/api/explore/v2.1/catalog/datasets/1_23-dnb-per-gemeente-en-per-sector/exports/json?lang=en&timezone=Europe%2FBrussels"

zipcode_data = {}
tarieven = []

def fetch_region_prices():
    global tarieven
    global zipcode_data
    for region in REGIONS_URLS_AFNAME:
        for name, url in region.items():
            response = requests.get(url)
            if response.status_code == 200:
                xls = pd.ExcelFile(BytesIO(response.content))
                df = xls.parse(xls.sheet_names[0])
                prices = df.iloc[45:58, 16].tolist()
                tarieven.append({name: prices})
            else:
                tarieven.append({name: None})
                print(f"Failed to fetch data for {name} from {url}")

    response = requests.get(ZIPCODE_DATA_URL)
    if response.status_code == 200:
        zipcode_data = response.json()
        return zipcode_data
    else:
        print(f"Failed to fetch data from {ZIPCODE_DATA_URL}")
        return None
    

from datetime import datetime

def get_cost_from_zip(zip=None):
    global tarieven
    global zipcode_data
    region = ""
    price = 0

    current_month = datetime.now().month
    
    for row in zipcode_data:
        if row["postcode"] == zip:
            region = row["dnb_elektriciteit"]

    for row in tarieven:
        if region in row:
            price = row[region][current_month - 1]

    return price
