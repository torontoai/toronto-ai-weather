"""
Main entry point for the Toronto AI Weather Flask application.

This module provides the main Flask application with routes and configuration.
It uses only pure Python dependencies for deployment compatibility.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
import json
import datetime
import random
import math

# Import pure Python utilities instead of native dependencies
from src.utils.pure_weather import get_current_weather, get_forecast, get_historical_data
from src.utils.pure_visualization import generate_chart_data, generate_map_data

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'toronto-ai-weather-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///toronto_weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
CORS(app)

# Import models after db initialization to avoid circular imports
from src.models.user import User
from src.models.device import Device

# Import routes
from src.routes.main import main_bp
from src.routes.auth import auth_bp
from src.routes.weather import weather_bp
from src.routes.api import api_bp
from src.routes.admin import admin_bp

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(weather_bp, url_prefix='/weather')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/admin')

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Context processor to add global variables to templates
@app.context_processor
def inject_globals():
    return {
        'app_name': 'Toronto AI Weather',
        'current_year': datetime.datetime.now().year,
        'device_count': Device.query.count(),
        'user_count': User.query.count()
    }

# Create database tables
with app.app_context():
    db.create_all()

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
