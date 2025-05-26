"""
Main entry point for the Toronto AI Weather web application.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from datetime import datetime, timedelta
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'toronto_ai_weather_secret_key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'toronto_ai_weather.db')}"

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import and register blueprints
from src.routes.auth import auth_bp
from src.routes.main import main_bp
from src.routes.api import api_bp
from src.routes.admin import admin_bp
from src.routes.weather import weather_bp

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(weather_bp, url_prefix='/weather')

# Import models
from src.models.user import User
from src.models.weather import WeatherData, Forecast, Location
from src.models.device import Device, DeviceContribution
from src.models.api import ApiKey, ApiUsage

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_now():
    """Add current time to all templates."""
    return {'now': datetime.utcnow()}

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"Server error: {e}")
    return render_template('errors/500.html'), 500

@app.before_request
def before_request():
    """Execute before each request."""
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=7)
    session.modified = True

@app.after_request
def after_request(response):
    """Execute after each request."""
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
