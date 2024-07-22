import os
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
from app.utils import normalize_column_name, rename_map

load_dotenv()


db_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME')
}

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

            # Drop rows where 'Jaar' value is empty
            combined_data = combined_data.dropna(subset=['jaar'])

            return combined_data
        except Exception as e:
            print(f"An error occurred: {e}")
            return pd.DataFrame()
    else:
        print("SRC_URL is not set in the .env file.")
        return pd.DataFrame()

data = fetch_data()

# Define possible columns and their default values
columns_with_defaults = {
    'jaar': None, 'maand': None, 'handelsnaam': None, 'productnaam': None, 'segment': None, 'energietype': None,
    'contracttype': None, 'vast_variabel_dynamisch': None, 'prijsonderdeel': None, 'indexatieparameter_x': None,
    'indexatieparameter_y': None, 'beschrijving_x': None, 'beschrijving_y': None, 'waarde_x_vreg': None,
    'waarde_y_vreg': None, 'waarde_x_laatst_gekende': None, 'waarde_y_laatst_gekende': None, 'a': None, 'b': None,
    'c': None, 'd': None, 'prijs': None
}

# Reorder and fill DataFrame columns
for col in columns_with_defaults:
    if col not in data.columns:
        data[col] = columns_with_defaults[col]

data = data[list(columns_with_defaults.keys())]

# Convert NaN to None and ensure correct data types
data = data.where(pd.notnull(data), None)

# Separate rows with "WKK", "groene stroom", and "Vaste vergoeding" in 'prijsonderdeel'
wkk_rows = data[data['prijsonderdeel'].str.contains("WKK", na=False)]
groene_stroom_rows = data[data['prijsonderdeel'].str.contains("groene stroom", na=False)]
vaste_vergoeding_rows = data[data['prijsonderdeel'].str.contains("Vaste vergoeding", na=False)]

# Remove "WKK", "groene stroom", and "Vaste vergoeding" rows from the original data
data = data[~data['prijsonderdeel'].str.contains("WKK|groene stroom|Vaste vergoeding", na=False)]

# Create columns for wkk, groene_stroom, and various vaste_vergoeding columns
data['wkk'] = None
data['groene_stroom'] = None
data['vaste_vergoeding'] = None
data['vaste_vergoeding_enkelvoudige_meter'] = None
data['vaste_vergoeding_tweevoudige_meter'] = None
data['vaste_vergoeding_uitsluitend_nachttarief'] = None

# Aggregate wkk and groene stroom values
for _, row in wkk_rows.iterrows():
    match = (data['segment'] == row['segment']) & \
            (data['energietype'] == row['energietype']) & \
            (data['contracttype'] == row['contracttype']) & \
            (data['handelsnaam'] == row['handelsnaam']) & \
            (data['productnaam'] == row['productnaam']) & \
            (data['jaar'] == row['jaar']) & \
            (data['maand'] == row['maand'])
    data.loc[match, 'wkk'] = row['prijs']

for _, row in groene_stroom_rows.iterrows():
    match = (data['segment'] == row['segment']) & \
            (data['energietype'] == row['energietype']) & \
            (data['contracttype'] == row['contracttype']) & \
            (data['handelsnaam'] == row['handelsnaam']) & \
            (data['productnaam'] == row['productnaam']) & \
            (data['jaar'] == row['jaar']) & \
            (data['maand'] == row['maand'])
    data.loc[match, 'groene_stroom'] = row['prijs']

# Aggregate vaste_vergoeding values
for _, row in vaste_vergoeding_rows.iterrows():
    col_name = row['prijsonderdeel'].lower().replace(' ', '_').replace('_(', '').replace(')', '').replace('€', '').replace('__', '_').strip()
    if col_name not in data.columns:
        continue
    match = (data['segment'] == row['segment']) & \
            (data['energietype'] == row['energietype']) & \
            (data['contracttype'] == row['contracttype']) & \
            (data['handelsnaam'] == row['handelsnaam']) & \
            (data['productnaam'] == row['productnaam']) & \
            (data['jaar'] == row['jaar']) & \
            (data['maand'] == row['maand'])
    data.loc[match, col_name] = row['prijs']

# Function to handle row conversion
def convert_row(row):
    # Convert row to list and replace any NaN with None
    return [None if pd.isna(x) else x for x in row]

# Connect to MySQL and insert data
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Create table if not exists
create_table_query = '''
CREATE TABLE IF NOT EXISTS data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    jaar VARCHAR(10),
    maand VARCHAR(12),
    handelsnaam VARCHAR(255),
    productnaam VARCHAR(255),
    segment VARCHAR(255),
    energietype VARCHAR(255),
    contracttype VARCHAR(255),
    vast_variabel_dynamisch VARCHAR(255),
    prijsonderdeel VARCHAR(255),
    indexatieparameter_x VARCHAR(255),
    indexatieparameter_y VARCHAR(255),
    beschrijving_x TEXT,
    beschrijving_y TEXT,
    waarde_x_vreg FLOAT,
    waarde_y_vreg FLOAT,
    waarde_x_laatst_gekende FLOAT,
    waarde_y_laatst_gekende FLOAT,
    a FLOAT,
    b FLOAT,
    c FLOAT,
    d FLOAT,
    prijs FLOAT,
    wkk FLOAT,
    groene_stroom FLOAT,
    vaste_vergoeding FLOAT,
    vaste_vergoeding_enkelvoudige_meter FLOAT,
    vaste_vergoeding_tweevoudige_meter FLOAT,
    vaste_vergoeding_uitsluitend_nachttarief FLOAT,
    UNIQUE (jaar, maand, handelsnaam, productnaam, prijsonderdeel)
);
'''
cursor.execute(create_table_query)

# Insert data into the table
insert_query = '''
INSERT INTO data (jaar, maand, handelsnaam, productnaam, segment, energietype, contracttype, vast_variabel_dynamisch,
    prijsonderdeel, indexatieparameter_x, indexatieparameter_y, beschrijving_x, beschrijving_y,
    waarde_x_vreg, waarde_y_vreg, waarde_x_laatst_gekende, waarde_y_laatst_gekende, a, b, c, d, prijs, wkk, groene_stroom, 
    vaste_vergoeding, vaste_vergoeding_enkelvoudige_meter, vaste_vergoeding_tweevoudige_meter, vaste_vergoeding_uitsluitend_nachttarief)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    segment=VALUES(segment),
    energietype=VALUES(energietype),
    contracttype=VALUES(contracttype),
    vast_variabel_dynamisch=VALUES(vast_variabel_dynamisch),
    indexatieparameter_x=VALUES(indexatieparameter_x),
    indexatieparameter_y=VALUES(indexatieparameter_y),
    beschrijving_x=VALUES(beschrijving_x),
    beschrijving_y=VALUES(beschrijving_y),
    waarde_x_vreg=VALUES(waarde_x_vreg),
    waarde_y_vreg=VALUES(waarde_y_vreg),
    waarde_x_laatst_gekende=VALUES(waarde_x_laatst_gekende),
    waarde_y_laatst_gekende=VALUES(waarde_y_laatst_gekende),
    a=VALUES(a),
    b=VALUES(b),
    c=VALUES(c),
    d=VALUES(d),
    prijs=VALUES(prijs),
    wkk=VALUES(wkk),
    groene_stroom=VALUES(groene_stroom),
    vaste_vergoeding=VALUES(vaste_vergoeding),
    vaste_vergoeding_enkelvoudige_meter=VALUES(vaste_vergoeding_enkelvoudige_meter),
    vaste_vergoeding_tweevoudige_meter=VALUES(vaste_vergoeding_tweevoudige_meter),
    vaste_vergoeding_uitsluitend_nachttarief=VALUES(vaste_vergoeding_uitsluitend_nachttarief);
'''

# Insert rows and log success or error
for _, row in data.iterrows():
    row_values = convert_row(row)
    try:
        cursor.execute(insert_query, row_values)
    except Exception as e:
        print(f"Error inserting row: {row_values}\nException: {e}")

conn.commit()

# Verification query
cursor.execute("SELECT COUNT(*) FROM data")
row_count = cursor.fetchone()[0]
print(f"Number of rows in the table: {row_count}")

cursor.close()
conn.close()
