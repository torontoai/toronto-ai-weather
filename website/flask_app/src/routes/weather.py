"""
Weather routes for Toronto AI Weather web application.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from src.main import db
from src.models.user import User, SavedLocation
from src.models.weather import Location, WeatherData, Forecast, WeatherAlert, PredictionAccuracy
from src.utils.weather import get_current_weather, get_forecast, get_historical_weather
from src.utils.visualization import generate_weather_chart, generate_forecast_chart

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/global')
def global_map():
    """Render the global weather map."""
    # Get recent global weather data for visualization
    return render_template(
        'weather/global_map.html',
        title='Global Weather Map'
    )

@weather_bp.route('/regional')
def regional_map():
    """Render the regional weather map."""
    # Get region from query parameters or default to user's region
    region = request.args.get('region')
    
    # If user is logged in and no region specified, use their default location
    if not region and current_user.is_authenticated:
        default_location = SavedLocation.query.filter_by(
            user_id=current_user.id,
            is_default=True
        ).first()
        
        if default_location:
            # Determine region from coordinates
            # This is a simplified approach - in production, would use a geocoding service
            region = "North America"  # Default fallback
    
    return render_template(
        'weather/regional_map.html',
        title=f'{region} Weather Map' if region else 'Regional Weather Map',
        region=region
    )

@weather_bp.route('/local')
def local_map():
    """Render the local weather map."""
    # Get location from query parameters
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    location_name = request.args.get('name', 'Local Area')
    
    # If user is logged in and no coordinates specified, use their default location
    if (not latitude or not longitude) and current_user.is_authenticated:
        default_location = SavedLocation.query.filter_by(
            user_id=current_user.id,
            is_default=True
        ).first()
        
        if default_location:
            latitude = default_location.latitude
            longitude = default_location.longitude
            location_name = default_location.name
    
    # If still no coordinates, use a default location
    if not latitude or not longitude:
        latitude = 43.6532  # Toronto
        longitude = -79.3832
        location_name = "Toronto"
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (ValueError, TypeError):
        flash('Invalid coordinates', 'danger')
        return redirect(url_for('weather.global_map'))
    
    # Get weather data for this location
    location = Location.query.filter_by(
        latitude=latitude,
        longitude=longitude
    ).first()
    
    weather_data = None
    forecast_data = None
    
    if location:
        weather_data = WeatherData.query.filter_by(
            location_id=location.id
        ).order_by(WeatherData.timestamp.desc()).first()
        
        forecast_data = Forecast.query.filter_by(
            location_id=location.id
        ).order_by(Forecast.forecast_timestamp.asc()).limit(24).all()
    
    # If no data in database, fetch from weather service
    if not weather_data:
        weather_data = get_current_weather(latitude, longitude)
    
    if not forecast_data:
        forecast_data = get_forecast(latitude, longitude)
    
    # Generate weather charts
    current_chart = None
    forecast_chart = None
    
    if weather_data:
        current_chart = generate_weather_chart(weather_data)
    
    if forecast_data:
        forecast_chart = generate_forecast_chart(forecast_data)
    
    return render_template(
        'weather/local_map.html',
        title=f'{location_name} Weather',
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        weather_data=weather_data,
        forecast_data=forecast_data,
        current_chart=current_chart,
        forecast_chart=forecast_chart
    )

@weather_bp.route('/detail/<int:location_id>')
def weather_detail(location_id):
    """Render detailed weather information for a location."""
    location = Location.query.get_or_404(location_id)
    
    # Get current weather
    weather_data = WeatherData.query.filter_by(
        location_id=location.id
    ).order_by(WeatherData.timestamp.desc()).first()
    
    # Get forecast
    forecast_data = Forecast.query.filter_by(
        location_id=location.id
    ).order_by(Forecast.forecast_timestamp.asc()).limit(24).all()
    
    # Get historical data for comparison
    historical_data = get_historical_weather(
        location.latitude,
        location.longitude,
        days_ago=7  # Compare to one week ago
    )
    
    # Get any active alerts
    alerts = WeatherAlert.query.filter_by(
        location_id=location.id
    ).filter(
        WeatherAlert.end_time > datetime.utcnow()
    ).all()
    
    # Generate charts
    current_chart = None
    forecast_chart = None
    historical_chart = None
    
    if weather_data:
        current_chart = generate_weather_chart(weather_data)
    
    if forecast_data:
        forecast_chart = generate_forecast_chart(forecast_data)
    
    if historical_data:
        historical_chart = generate_weather_chart(historical_data, is_historical=True)
    
    return render_template(
        'weather/detail.html',
        title=f'{location.name} Weather Details',
        location=location,
        weather_data=weather_data,
        forecast_data=forecast_data,
        historical_data=historical_data,
        alerts=alerts,
        current_chart=current_chart,
        forecast_chart=forecast_chart,
        historical_chart=historical_chart
    )

@weather_bp.route('/accuracy')
def accuracy_stats():
    """Render prediction accuracy statistics."""
    # Get overall system accuracy
    overall_accuracy = db.session.query(
        db.func.avg(PredictionAccuracy.overall_accuracy)
    ).scalar() or 0.0
    
    # Get accuracy by prediction type
    temperature_accuracy = db.session.query(
        db.func.avg(1.0 - PredictionAccuracy.temperature_error)
    ).scalar() or 0.0
    
    humidity_accuracy = db.session.query(
        db.func.avg(1.0 - PredictionAccuracy.humidity_error)
    ).scalar() or 0.0
    
    precipitation_accuracy = db.session.query(
        db.func.avg(1.0 - PredictionAccuracy.precipitation_error)
    ).scalar() or 0.0
    
    # Get accuracy trend over time
    accuracy_trend = db.session.query(
        db.func.date(PredictionAccuracy.created_at),
        db.func.avg(PredictionAccuracy.overall_accuracy)
    ).group_by(
        db.func.date(PredictionAccuracy.created_at)
    ).order_by(
        db.func.date(PredictionAccuracy.created_at)
    ).limit(30).all()
    
    return render_template(
        'weather/accuracy.html',
        title='Prediction Accuracy',
        overall_accuracy=overall_accuracy,
        temperature_accuracy=temperature_accuracy,
        humidity_accuracy=humidity_accuracy,
        precipitation_accuracy=precipitation_accuracy,
        accuracy_trend=accuracy_trend
    )

@weather_bp.route('/alerts')
def alerts():
    """Render active weather alerts."""
    # Get all active alerts
    active_alerts = WeatherAlert.query.filter(
        WeatherAlert.end_time > datetime.utcnow()
    ).order_by(
        WeatherAlert.severity,
        WeatherAlert.start_time
    ).all()
    
    # If user is logged in, highlight alerts for their saved locations
    user_location_alerts = []
    if current_user.is_authenticated:
        saved_locations = SavedLocation.query.filter_by(
            user_id=current_user.id
        ).all()
        
        for saved_location in saved_locations:
            # Find the corresponding location in the database
            location = Location.query.filter_by(
                latitude=saved_location.latitude,
                longitude=saved_location.longitude
            ).first()
            
            if location:
                # Get alerts for this location
                location_alerts = WeatherAlert.query.filter_by(
                    location_id=location.id
                ).filter(
                    WeatherAlert.end_time > datetime.utcnow()
                ).all()
                
                if location_alerts:
                    user_location_alerts.append({
                        'saved_location': saved_location,
                        'alerts': location_alerts
                    })
    
    return render_template(
        'weather/alerts.html',
        title='Weather Alerts',
        active_alerts=active_alerts,
        user_location_alerts=user_location_alerts
    )

@weather_bp.route('/api/weather/current')
def api_current_weather():
    """API endpoint for current weather data."""
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    
    if not latitude or not longitude:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400
    
    # Get weather data
    location = Location.query.filter_by(
        latitude=latitude,
        longitude=longitude
    ).first()
    
    if location:
        weather_data = WeatherData.query.filter_by(
            location_id=location.id
        ).order_by(WeatherData.timestamp.desc()).first()
        
        if weather_data:
            return jsonify(weather_data.to_dict()), 200
    
    # If no data in database, fetch from weather service
    weather_data = get_current_weather(latitude, longitude)
    
    if weather_data:
        return jsonify(weather_data.to_dict()), 200
    else:
        return jsonify({'error': 'Weather data not available'}), 404

@weather_bp.route('/api/weather/forecast')
def api_forecast():
    """API endpoint for weather forecast data."""
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    hours = request.args.get('hours', 24)
    
    if not latitude or not longitude:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
        hours = int(hours)
    except ValueError:
        return jsonify({'error': 'Invalid parameters'}), 400
    
    # Get forecast data
    location = Location.query.filter_by(
        latitude=latitude,
        longitude=longitude
    ).first()
    
    if location:
        forecast_data = Forecast.query.filter_by(
            location_id=location.id
        ).filter(
            Forecast.forecast_timestamp > datetime.utcnow()
        ).order_by(
            Forecast.forecast_timestamp
        ).limit(hours).all()
        
        if forecast_data:
            return jsonify([f.to_dict() for f in forecast_data]), 200
    
    # If no data in database, fetch from weather service
    forecast_data = get_forecast(latitude, longitude, hours=hours)
    
    if forecast_data:
        return jsonify([f.to_dict() for f in forecast_data]), 200
    else:
        return jsonify({'error': 'Forecast data not available'}), 404
