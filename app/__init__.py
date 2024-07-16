from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import SchedulerNotRunningError
import os
from .entsoe import update_entsoe_data
from .netkosten import fetch_region_prices

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from . import routes
        db.create_all()
        update_entsoe_data()
        fetch_region_prices()

    scheduler = BackgroundScheduler()
    scheduler.add_job(update_entsoe_data, 'interval', hours=1)
    scheduler.add_job(fetch_region_prices, 'interval', days=1)
    scheduler.start()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        try:
            if scheduler.running:
                scheduler.shutdown()
        except SchedulerNotRunningError:
            print("Scheduler was not running.")

    return app
