from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import SchedulerNotRunningError
import os
from .entsoe import update_entsoe_data

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from . import routes  # Import routes
        db.create_all()
        update_entsoe_data()  # Initialize data on startup

    # Schedule the ENTSO-E data update
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_entsoe_data, 'interval', hours=1)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        try:
            if scheduler.running:
                scheduler.shutdown()
        except SchedulerNotRunningError:
            print("Scheduler was not running.")

    return app
