"""
Main routes for Toronto AI Weather.

This module provides the main routes for the Toronto AI Weather application.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
import json
import datetime
import random

# Import pure Python utilities
from src.utils.pure_weather import get_current_weather, get_forecast, get_historical_data
from src.utils.pure_visualization import generate_chart_data, generate_map_data
from src.utils.distributed import register_device, get_device_stats, assign_task

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the homepage."""
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Render the user dashboard."""
    # Get user's location (default to Toronto if not set)
    user_location = session.get('user_location', {'latitude': 43.6532, 'longitude': -79.3832})
    
    # Get current weather for user's location
    current_weather = get_current_weather(user_location['latitude'], user_location['longitude'])
    
    # Get forecast for user's location
    forecast = get_forecast(user_location['latitude'], user_location['longitude'], hours=24)
    
    # Get device stats if user has registered devices
    device_stats = get_device_stats(current_user.id) if current_user.is_authenticated else None
    
    # Generate chart data
    temperature_chart = generate_chart_data('temperature_forecast', user_location)
    precipitation_chart = generate_chart_data('precipitation_forecast', user_location)
    system_metrics = generate_chart_data('system_metrics')
    
    return render_template(
        'dashboard.html',
        current_weather=current_weather,
        forecast=forecast,
        device_stats=device_stats,
        temperature_chart=json.dumps(temperature_chart),
        precipitation_chart=json.dumps(precipitation_chart),
        system_metrics=json.dumps(system_metrics),
        user_location=user_location
    )

@main_bp.route('/global-map')
def global_map():
    """Render the global weather map."""
    # Get map center (default to Toronto if not set)
    map_center = session.get('map_center', {'latitude': 43.6532, 'longitude': -79.3832})
    
    # Generate map data
    temperature_map = generate_map_data('temperature', map_center)
    precipitation_map = generate_map_data('precipitation', map_center)
    wind_map = generate_map_data('wind', map_center)
    
    return render_template(
        'global_map.html',
        temperature_map=json.dumps(temperature_map),
        precipitation_map=json.dumps(precipitation_map),
        wind_map=json.dumps(wind_map),
        map_center=map_center
    )

@main_bp.route('/set-location', methods=['POST'])
def set_location():
    """Set user's location."""
    data = request.get_json()
    
    if 'latitude' in data and 'longitude' in data:
        session['user_location'] = {
            'latitude': float(data['latitude']),
            'longitude': float(data['longitude'])
        }
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid location data'})

@main_bp.route('/register-device', methods=['POST'])
@login_required
def register_device_route():
    """Register a device for distributed computation."""
    data = request.get_json()
    
    if 'device_type' in data and 'browser_type' in data:
        device_id = register_device(
            user_id=current_user.id,
            device_type=data['device_type'],
            os_type=data.get('os_type', 'unknown'),
            browser_type=data['browser_type'],
            ip_address=request.remote_addr
        )
        
        return jsonify({'success': True, 'device_id': device_id})
    
    return jsonify({'success': False, 'error': 'Invalid device data'})

@main_bp.route('/get-task', methods=['POST'])
def get_task():
    """Get a computation task for a device."""
    data = request.get_json()
    
    if 'device_id' in data:
        task = assign_task(data['device_id'])
        return jsonify({'success': True, 'task': task})
    
    return jsonify({'success': False, 'error': 'Invalid device ID'})

@main_bp.route('/submit-task-result', methods=['POST'])
def submit_task_result():
    """Submit the result of a computation task."""
    data = request.get_json()
    
    if 'device_id' in data and 'task_id' in data and 'result' in data:
        # Process task result
        # In a real implementation, this would update the distributed computation system
        
        # For demo purposes, just return success
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid task result data'})

@main_bp.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Render the contact page."""
    return render_template('contact.html')
