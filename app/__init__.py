from flask import Flask
from dotenv import load_dotenv
import os
import pandas as pd
from app.utils import normalize_column_name, fetch_data, rename_map

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Load data on server startup
    app.data = fetch_data()

    with app.app_context():
        from . import routes  # Import routes

    return app
