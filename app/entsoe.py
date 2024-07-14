import os
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz


ENTSOE_API_URL = os.getenv('ENTSOE_API_URL')
ENTSOE_API_KEY = os.getenv('ENTSOE_API_KEY')
LOCAL_TIMEZONE = pytz.timezone('Europe/Brussels')

def fetch_entsoe_data():
    current_date = datetime.now(pytz.UTC)
    period_start = current_date.strftime('%Y%m%d0000')
    period_end = (current_date + timedelta(days=1)).strftime('%Y%m%d0000')
    
    url = f"{ENTSOE_API_URL}periodStart={period_start}&periodEnd={period_end}&securityToken=af42286a-cd40-4df2-85d1-ade8083fb4fc"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code}")
        return None
    
    root = ET.fromstring(response.content)
    data = parse_entsoe_data(root)
    return data

def parse_entsoe_data(root):
    data = []
    for period in root.findall(".//{*}Period"):
        time_interval = period.find("{*}timeInterval")
        start_utc = datetime.strptime(time_interval.find("{*}start").text, '%Y-%m-%dT%H:%MZ').replace(tzinfo=pytz.UTC)
        
        for point in period.findall("{*}Point"):
            position = int(point.find("{*}position").text)
            price = point.find("{*}price.amount").text

            hour_start_utc = start_utc + timedelta(hours=position-1)
            hour_end_utc = hour_start_utc + timedelta(hours=1)

            hour_start_local = hour_start_utc.astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%dT%H:%M:%S%z')
            hour_end_local = hour_end_utc.astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%dT%H:%M:%S%z')
            
            data.append({
                'start': hour_start_local,
                'end': hour_end_local,
                'position': position,
                'price': price
            })
    return data

entsoe_data = []

def get_entsoe_data():
    global entsoe_data
    return entsoe_data

def update_entsoe_data():
    global entsoe_data
    entsoe_data = fetch_entsoe_data()
