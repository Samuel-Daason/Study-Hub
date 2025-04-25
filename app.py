from flask import Flask, render_template, send_from_directory, request, redirect
from models import db, Subject, User
from catalogue_routes import catalogue_routes, view_papers
from flask_login import LoginManager
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Starting the Flask App
app = Flask(__name__)

# Secret Key for runtime and cookies
app.config['SECRET_KEY'] = '1423'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalogue.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# Specify login route in the blueprint
login_manager.login_view = "catalogue_routes.login"
login_manager.login_message = ""

# Define the user loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Cascade deletion for SQLite Database
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

# Starting the database
db.init_app(app)

# View all papers in a subject
@app.route('/<subject_name>')
def subject_page(subject_name):
    return view_papers(subject_name)

# Serve custom JS
@app.route('/scripts/<path:path>')
def send_js(path):
    return send_from_directory('scripts/js', path)

# Register paper-related routes
app.register_blueprint(catalogue_routes, url_prefix='')

# Create the database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
