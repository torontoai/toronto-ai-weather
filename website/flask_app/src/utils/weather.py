"""
Utility functions for weather data processing and retrieval.
"""

import requests
import json
from datetime import datetime, timedelta
import logging

from src.main import db
from src.models.weather import Location, WeatherData, Forecast

logger = logging.getLogger(__name__)

def get_current_weather(latitude, longitude):
    """
    Get current weather for a location.
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
        
    Returns:
        WeatherData: Weather data object or None if retrieval fails
    """
    try:
        # Check if location exists in database
        location = Location.query.filter_by(
            latitude=latitude,
            longitude=longitude
        ).first()
        
        # If location doesn't exist, create it
        if not location:
            # Get location name from coordinates using reverse geocoding
            location_name = get_location_name(latitude, longitude)
            
            location = Location(
                name=location_name,
                latitude=latitude,
                longitude=longitude,
                country=get_country_from_coordinates(latitude, longitude),
                region=get_region_from_coordinates(latitude, longitude),
                city=get_city_from_coordinates(latitude, longitude),
                timezone=get_timezone_from_coordinates(latitude, longitude)
            )
            
            db.session.add(location)
            db.session.commit()
        
        # Simulate weather data retrieval from external API
        # In a real implementation, this would call an actual weather API
        weather_data = simulate_weather_data(latitude, longitude)
        
        # Create WeatherData object
        weather = WeatherData(
            location_id=location.id,
            temperature=weather_data['temperature'],
            feels_like=weather_data['feels_like'],
            humidity=weather_data['humidity'],
            pressure=weather_data['pressure'],
            wind_speed=weather_data['wind_speed'],
            wind_direction=weather_data['wind_direction'],
            weather_condition=weather_data['weather_condition'],
            weather_description=weather_data['weather_description'],
            weather_icon=weather_data['weather_icon'],
            cloud_coverage=weather_data['cloud_coverage'],
            visibility=weather_data['visibility'],
            uv_index=weather_data['uv_index'],
            precipitation=weather_data['precipitation'],
            dew_point=weather_data['dew_point'],
            source='simulated',
            accuracy=0.95
        )
        
        db.session.add(weather)
        db.session.commit()
        
        return weather
    
    except Exception as e:
        logger.error(f"Error getting current weather: {e}")
        return None

def get_forecast(latitude, longitude, hours=24):
    """
    Get weather forecast for a location.
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
        hours (int): Number of hours to forecast
        
    Returns:
        list: List of Forecast objects or None if retrieval fails
    """
    try:
        # Check if location exists in database
        location = Location.query.filter_by(
            latitude=latitude,
            longitude=longitude
        ).first()
        
        # If location doesn't exist, create it
        if not location:
            # Get location name from coordinates using reverse geocoding
            location_name = get_location_name(latitude, longitude)
            
            location = Location(
                name=location_name,
                latitude=latitude,
                longitude=longitude,
                country=get_country_from_coordinates(latitude, longitude),
                region=get_region_from_coordinates(latitude, longitude),
                city=get_city_from_coordinates(latitude, longitude),
                timezone=get_timezone_from_coordinates(latitude, longitude)
            )
            
            db.session.add(location)
            db.session.commit()
        
        # Simulate forecast data retrieval from external API
        # In a real implementation, this would call an actual weather API
        forecast_data = simulate_forecast_data(latitude, longitude, hours)
        
        forecasts = []
        
        for hour_data in forecast_data:
            forecast = Forecast(
                location_id=location.id,
                forecast_timestamp=hour_data['timestamp'],
                temperature=hour_data['temperature'],
                feels_like=hour_data['feels_like'],
                humidity=hour_data['humidity'],
                pressure=hour_data['pressure'],
                wind_speed=hour_data['wind_speed'],
                wind_direction=hour_data['wind_direction'],
                weather_condition=hour_data['weather_condition'],
                weather_description=hour_data['weather_description'],
                weather_icon=hour_data['weather_icon'],
                cloud_coverage=hour_data['cloud_coverage'],
                visibility=hour_data['visibility'],
                uv_index=hour_data['uv_index'],
                precipitation_probability=hour_data['precipitation_probability'],
                precipitation_amount=hour_data['precipitation_amount'],
                dew_point=hour_data['dew_point'],
                confidence=hour_data['confidence'],
                model_version='v1.0'
            )
            
            db.session.add(forecast)
            forecasts.append(forecast)
        
        db.session.commit()
        
        return forecasts
    
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        return None

def get_historical_weather(latitude, longitude, days_ago=7):
    """
    Get historical weather data for a location.
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
        days_ago (int): Number of days in the past
        
    Returns:
        WeatherData: Historical weather data or None if retrieval fails
    """
    try:
        # Check if location exists in database
        location = Location.query.filter_by(
            latitude=latitude,
            longitude=longitude
        ).first()
        
        if not location:
            return None
        
        # Check if we have historical data in the database
        historical_date = datetime.utcnow() - timedelta(days=days_ago)
        
        historical_data = WeatherData.query.filter_by(
            location_id=location.id
        ).filter(
            WeatherData.timestamp >= historical_date.replace(hour=0, minute=0, second=0),
            WeatherData.timestamp <= historical_date.replace(hour=23, minute=59, second=59)
        ).first()
        
        if historical_data:
            return historical_data
        
        # If no data in database, simulate historical data
        weather_data = simulate_weather_data(
            latitude, 
            longitude, 
            timestamp=historical_date
        )
        
        # Create WeatherData object
        weather = WeatherData(
            location_id=location.id,
            timestamp=historical_date,
            temperature=weather_data['temperature'],
            feels_like=weather_data['feels_like'],
            humidity=weather_data['humidity'],
            pressure=weather_data['pressure'],
            wind_speed=weather_data['wind_speed'],
            wind_direction=weather_data['wind_direction'],
            weather_condition=weather_data['weather_condition'],
            weather_description=weather_data['weather_description'],
            weather_icon=weather_data['weather_icon'],
            cloud_coverage=weather_data['cloud_coverage'],
            visibility=weather_data['visibility'],
            uv_index=weather_data['uv_index'],
            precipitation=weather_data['precipitation'],
            dew_point=weather_data['dew_point'],
            source='simulated_historical',
            accuracy=0.90
        )
        
        db.session.add(weather)
        db.session.commit()
        
        return weather
    
    except Exception as e:
        logger.error(f"Error getting historical weather: {e}")
        return None

def get_location_name(latitude, longitude):
    """
    Get location name from coordinates using reverse geocoding.
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
        
    Returns:
        str: Location name
    """
    # In a real implementation, this would call a geocoding API
    # For now, return a placeholder based on coordinates
    return f"Location at {latitude:.2f}, {longitude:.2f}"

def get_country_from_coordinates(latitude, longitude):
    """Get country from coordinates."""
    # Placeholder implementation
    return "Unknown Country"

def get_region_from_coordinates(latitude, longitude):
    """Get region from coordinates."""
    # Placeholder implementation
    return "Unknown Region"

def get_city_from_coordinates(latitude, longitude):
    """Get city from coordinates."""
    # Placeholder implementation
    return "Unknown City"

def get_timezone_from_coordinates(latitude, longitude):
    """Get timezone from coordinates."""
    # Placeholder implementation
    return "UTC"

def simulate_weather_data(latitude, longitude, timestamp=None):
    """
    Simulate weather data for testing purposes.
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
        timestamp (datetime): Optional timestamp for historical data
        
    Returns:
        dict: Simulated weather data
    """
    import random
    
    # Use timestamp if provided, otherwise use current time
    current_time = timestamp or datetime.utcnow()
    
    # Base temperature on latitude (colder at poles, warmer at equator)
    base_temp = 30 - abs(latitude) * 0.6
    
    # Add seasonal variation (northern/southern hemisphere)
    month = current_time.month
    if latitude > 0:  # Northern hemisphere
        seasonal_offset = 10 * math.sin((month - 1) * math.pi / 6)
    else:  # Southern hemisphere
        seasonal_offset = 10 * math.sin((month - 7) * math.pi / 6)
    
    # Add daily variation (warmer during day, cooler at night)
    hour = current_time.hour
    daily_offset = 5 * math.sin((hour - 6) * math.pi / 12)
    
    # Add some randomness
    random_offset = random.uniform(-3, 3)
    
    temperature = base_temp + seasonal_offset + daily_offset + random_offset
    
    # Generate other weather parameters based on temperature
    if temperature < 0:
        weather_condition = "Snow"
        weather_description = "Light snow"
        weather_icon = "13d"
        precipitation = random.uniform(0, 5)
        precipitation_probability = random.uniform(0.3, 0.8)
    elif temperature < 10:
        weather_condition = "Clouds"
        weather_description = "Overcast clouds"
        weather_icon = "04d"
        precipitation = random.uniform(0, 2)
        precipitation_probability = random.uniform(0.1, 0.4)
    elif temperature < 20:
        weather_condition = "Clear"
        weather_description = "Clear sky"
        weather_icon = "01d"
        precipitation = 0
        precipitation_probability = random.uniform(0, 0.1)
    else:
        weather_condition = "Clear"
        weather_description = "Clear sky"
        weather_icon = "01d"
        precipitation = 0
        precipitation_probability = random.uniform(0, 0.05)
    
    # Generate other parameters
    humidity = random.uniform(30, 90)
    pressure = random.uniform(990, 1030)
    wind_speed = random.uniform(0, 15)
    wind_direction = random.uniform(0, 360)
    cloud_coverage = random.uniform(0, 100)
    visibility = random.uniform(5000, 10000)
    uv_index = random.uniform(0, 10)
    dew_point = temperature - random.uniform(5, 15)
    feels_like = temperature + random.uniform(-3, 3)
    
    return {
        'temperature': temperature,
        'feels_like': feels_like,
        'humidity': humidity,
        'pressure': pressure,
        'wind_speed': wind_speed,
        'wind_direction': wind_direction,
        'weather_condition': weather_condition,
        'weather_description': weather_description,
        'weather_icon': weather_icon,
        'cloud_coverage': cloud_coverage,
        'visibility': visibility,
        'uv_index': uv_index,
        'precipitation': precipitation,
        'precipitation_probability': precipitation_probability,
        'precipitation_amount': precipitation,
        'dew_point': dew_point,
        'confidence': random.uniform(0.7, 0.98)
    }

def simulate_forecast_data(latitude, longitude, hours=24):
    """
    Simulate forecast data for testing purposes.
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
        hours (int): Number of hours to forecast
        
    Returns:
        list: List of hourly forecast data
    """
    forecast = []
    
    for hour in range(hours):
        timestamp = datetime.utcnow() + timedelta(hours=hour)
        
        # Get simulated weather for this hour
        weather = simulate_weather_data(latitude, longitude, timestamp)
        weather['timestamp'] = timestamp
        
        forecast.append(weather)
    
    return forecast

# Import math module for trigonometric functions
import math
