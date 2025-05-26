"""
Main routes for Toronto AI Weather web application.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from src.main import db
from src.models.user import User, SavedLocation
from src.models.weather import Location, WeatherData, Forecast
from src.models.device import Device, DeviceContribution, SystemMetrics
from src.utils.weather import get_current_weather, get_forecast

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the homepage."""
    # Get system metrics for display
    metrics = SystemMetrics.query.order_by(SystemMetrics.timestamp.desc()).first()
    
    # Get global weather highlights
    highlights = []
    
    return render_template(
        'main/index.html', 
        title='Home',
        metrics=metrics,
        highlights=highlights
    )

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Render the user dashboard."""
    # Get user's saved locations
    locations = SavedLocation.query.filter_by(user_id=current_user.id).all()
    
    # Get default location or first saved location
    default_location = SavedLocation.query.filter_by(
        user_id=current_user.id, 
        is_default=True
    ).first()
    
    if not default_location and locations:
        default_location = locations[0]
    
    # Get user's device contributions
    devices = Device.query.filter_by(user_id=current_user.id).all()
    
    device_contributions = []
    for device in devices:
        contributions = DeviceContribution.query.filter_by(
            device_id=device.id
        ).order_by(DeviceContribution.created_at.desc()).limit(10).all()
        
        device_contributions.append({
            'device': device,
            'contributions': contributions
        })
    
    # Get weather data for default location
    weather_data = None
    forecast_data = None
    
    if default_location:
        location = Location.query.filter_by(
            latitude=default_location.latitude,
            longitude=default_location.longitude
        ).first()
        
        if location:
            weather_data = WeatherData.query.filter_by(
                location_id=location.id
            ).order_by(WeatherData.timestamp.desc()).first()
            
            forecast_data = Forecast.query.filter_by(
                location_id=location.id
            ).order_by(Forecast.forecast_timestamp.asc()).limit(24).all()
    
    return render_template(
        'main/dashboard.html',
        title='Dashboard',
        locations=locations,
        default_location=default_location,
        device_contributions=device_contributions,
        weather_data=weather_data,
        forecast_data=forecast_data
    )

@main_bp.route('/profile')
@login_required
def profile():
    """Render the user profile page."""
    # Get user's API keys if they have API access
    api_keys = []
    if current_user.can_access_api():
        from src.models.api import ApiKey
        api_keys = ApiKey.query.filter_by(user_id=current_user.id).all()
    
    # Get user's devices
    devices = Device.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'main/profile.html',
        title='Profile',
        api_keys=api_keys,
        devices=devices
    )

@main_bp.route('/locations')
@login_required
def locations():
    """Render the locations management page."""
    # Get user's saved locations
    saved_locations = SavedLocation.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'main/locations.html',
        title='Manage Locations',
        locations=saved_locations
    )

@main_bp.route('/add-location', methods=['POST'])
@login_required
def add_location():
    """Add a new saved location."""
    name = request.form.get('name')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    is_default = request.form.get('is_default') == 'on'
    
    if not all([name, latitude, longitude]):
        flash('All fields are required', 'danger')
        return redirect(url_for('main.locations'))
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        flash('Invalid coordinates', 'danger')
        return redirect(url_for('main.locations'))
    
    # If this is the default location, unset any existing default
    if is_default:
        SavedLocation.query.filter_by(
            user_id=current_user.id,
            is_default=True
        ).update({'is_default': False})
    
    # Create new saved location
    location = SavedLocation(
        user_id=current_user.id,
        name=name,
        latitude=latitude,
        longitude=longitude,
        is_default=is_default
    )
    
    db.session.add(location)
    db.session.commit()
    
    flash('Location added successfully', 'success')
    return redirect(url_for('main.locations'))

@main_bp.route('/delete-location/<int:location_id>', methods=['POST'])
@login_required
def delete_location(location_id):
    """Delete a saved location."""
    location = SavedLocation.query.filter_by(
        id=location_id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(location)
    db.session.commit()
    
    flash('Location deleted successfully', 'success')
    return redirect(url_for('main.locations'))

@main_bp.route('/set-default-location/<int:location_id>', methods=['POST'])
@login_required
def set_default_location(location_id):
    """Set a location as the default."""
    # Unset any existing default
    SavedLocation.query.filter_by(
        user_id=current_user.id,
        is_default=True
    ).update({'is_default': False})
    
    # Set new default
    location = SavedLocation.query.filter_by(
        id=location_id,
        user_id=current_user.id
    ).first_or_404()
    
    location.is_default = True
    db.session.commit()
    
    flash('Default location updated successfully', 'success')
    return redirect(url_for('main.locations'))

@main_bp.route('/register-device', methods=['POST'])
@login_required
def register_device():
    """Register a new device for distributed computation."""
    device_name = request.form.get('device_name')
    device_type = request.form.get('device_type')
    max_resource_allocation = request.form.get('max_resource_allocation')
    
    if not all([device_name, device_type, max_resource_allocation]):
        flash('All fields are required', 'danger')
        return redirect(url_for('main.profile'))
    
    try:
        max_resource_allocation = float(max_resource_allocation) / 100.0  # Convert percentage to decimal
    except ValueError:
        flash('Invalid resource allocation value', 'danger')
        return redirect(url_for('main.profile'))
    
    # Create new device
    device = Device(
        user_id=current_user.id,
        device_uuid=f"manual_{datetime.utcnow().timestamp()}",
        device_name=device_name,
        device_type=device_type,
        max_resource_allocation=max_resource_allocation
    )
    
    db.session.add(device)
    db.session.commit()
    
    flash('Device registered successfully', 'success')
    return redirect(url_for('main.profile'))

@main_bp.route('/delete-device/<int:device_id>', methods=['POST'])
@login_required
def delete_device(device_id):
    """Delete a registered device."""
    device = Device.query.filter_by(
        id=device_id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(device)
    db.session.commit()
    
    flash('Device deleted successfully', 'success')
    return redirect(url_for('main.profile'))

@main_bp.route('/about')
def about():
    """Render the about page."""
    return render_template('main/about.html', title='About')

@main_bp.route('/contact')
def contact():
    """Render the contact page."""
    return render_template('main/contact.html', title='Contact')

@main_bp.route('/terms')
def terms():
    """Render the terms of service page."""
    return render_template('main/terms.html', title='Terms of Service')

@main_bp.route('/privacy')
def privacy():
    """Render the privacy policy page."""
    return render_template('main/privacy.html', title='Privacy Policy')
