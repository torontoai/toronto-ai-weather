"""
Pure Python visualization utilities for Toronto AI Weather.

This module provides visualization utilities using JavaScript-based solutions
instead of matplotlib or other native visualization libraries.
"""

import json
import random
import math
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union


def generate_chart_data(data_type: str, location: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate chart data for JavaScript visualization.
    
    Args:
        data_type: Type of chart data to generate
        location: Optional location information
        
    Returns:
        Dict with chart data in a format suitable for JavaScript charts
    """
    if data_type == 'temperature_forecast':
        return _generate_temperature_forecast(location)
    elif data_type == 'precipitation_forecast':
        return _generate_precipitation_forecast(location)
    elif data_type == 'system_metrics':
        return _generate_system_metrics()
    elif data_type == 'prediction_accuracy':
        return _generate_prediction_accuracy()
    elif data_type == 'device_contribution':
        return _generate_device_contribution()
    else:
        raise ValueError(f"Unknown chart data type: {data_type}")


def _generate_temperature_forecast(location: Optional[Dict] = None) -> Dict[str, Any]:
    """Generate temperature forecast chart data."""
    # Default location if none provided
    if not location:
        location = {'latitude': 43.6532, 'longitude': -79.3832}  # Toronto
    
    # Generate 24-hour forecast
    hours = 24
    now = datetime.datetime.now()
    
    # Labels (hours)
    labels = [(now + datetime.timedelta(hours=i)).strftime('%H:%M') for i in range(hours)]
    
    # Temperature data
    base_temp = 20 + random.uniform(-5, 5)  # Base temperature around 20°C
    temperatures = []
    
    for i in range(hours):
        hour = (now + datetime.timedelta(hours=i)).hour
        # Diurnal variation (cooler at night, warmer during day)
        diurnal_factor = math.sin(math.pi * (hour - 4) / 12)
        temp = base_temp + (5 * diurnal_factor) + random.uniform(-1, 1)
        temperatures.append(round(temp, 1))
    
    # Feels like temperature (usually slightly different)
    feels_like = [t + random.uniform(-2, 2) for t in temperatures]
    feels_like = [round(t, 1) for t in feels_like]
    
    return {
        'labels': labels,
        'datasets': [
            {
                'label': 'Temperature (°C)',
                'data': temperatures,
                'borderColor': '#FF6B6B',
                'backgroundColor': 'rgba(255, 107, 107, 0.2)',
                'fill': True
            },
            {
                'label': 'Feels Like (°C)',
                'data': feels_like,
                'borderColor': '#FF9E7A',
                'backgroundColor': 'rgba(255, 158, 122, 0.1)',
                'fill': True
            }
        ]
    }


def _generate_precipitation_forecast(location: Optional[Dict] = None) -> Dict[str, Any]:
    """Generate precipitation forecast chart data."""
    # Default location if none provided
    if not location:
        location = {'latitude': 43.6532, 'longitude': -79.3832}  # Toronto
    
    # Generate 24-hour forecast
    hours = 24
    now = datetime.datetime.now()
    
    # Labels (hours)
    labels = [(now + datetime.timedelta(hours=i)).strftime('%H:%M') for i in range(hours)]
    
    # Precipitation probability
    precipitation_prob = []
    
    # Generate a few rain events
    rain_start = random.randint(0, hours - 6)
    rain_duration = random.randint(2, 6)
    
    for i in range(hours):
        if i >= rain_start and i < rain_start + rain_duration:
            # During rain event
            prob = random.uniform(0.6, 0.9)
        else:
            # Outside rain event
            prob = random.uniform(0, 0.3)
        
        precipitation_prob.append(round(prob * 100))  # Convert to percentage
    
    # Precipitation amount (mm)
    precipitation_amount = []
    
    for prob in precipitation_prob:
        if prob > 50:
            # Higher probability means more rain
            amount = (prob / 100) * random.uniform(1, 5)
        else:
            # Lower probability means little to no rain
            amount = (prob / 100) * random.uniform(0, 1)
        
        precipitation_amount.append(round(amount, 1))
    
    return {
        'labels': labels,
        'datasets': [
            {
                'label': 'Precipitation Probability (%)',
                'data': precipitation_prob,
                'borderColor': '#4D96FF',
                'backgroundColor': 'rgba(77, 150, 255, 0.2)',
                'fill': True,
                'yAxisID': 'y'
            },
            {
                'label': 'Precipitation Amount (mm)',
                'data': precipitation_amount,
                'borderColor': '#6979F8',
                'backgroundColor': 'rgba(105, 121, 248, 0.2)',
                'fill': True,
                'yAxisID': 'y1'
            }
        ]
    }


def _generate_system_metrics() -> Dict[str, Any]:
    """Generate system metrics chart data."""
    # Generate 7-day metrics
    days = 7
    now = datetime.datetime.now()
    
    # Labels (days)
    labels = [(now - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
    
    # Active devices
    base_devices = 10000
    active_devices = []
    
    for i in range(days):
        # Gradually increasing trend with some randomness
        devices = base_devices + (i * 500) + random.randint(-200, 200)
        active_devices.append(devices)
    
    # System load
    system_load = []
    
    for i in range(days):
        # System load between 50% and 80%
        load = random.uniform(0.5, 0.8)
        system_load.append(round(load * 100))  # Convert to percentage
    
    # Prediction accuracy
    prediction_accuracy = []
    
    for i in range(days):
        # Accuracy between 85% and 95%
        accuracy = random.uniform(0.85, 0.95)
        prediction_accuracy.append(round(accuracy * 100, 1))  # Convert to percentage
    
    return {
        'labels': labels,
        'datasets': [
            {
                'label': 'Active Devices',
                'data': active_devices,
                'borderColor': '#4CAF50',
                'backgroundColor': 'rgba(76, 175, 80, 0.2)',
                'fill': True,
                'yAxisID': 'y'
            },
            {
                'label': 'System Load (%)',
                'data': system_load,
                'borderColor': '#FF9800',
                'backgroundColor': 'rgba(255, 152, 0, 0.2)',
                'fill': True,
                'yAxisID': 'y1'
            },
            {
                'label': 'Prediction Accuracy (%)',
                'data': prediction_accuracy,
                'borderColor': '#2196F3',
                'backgroundColor': 'rgba(33, 150, 243, 0.2)',
                'fill': True,
                'yAxisID': 'y1'
            }
        ]
    }


def _generate_prediction_accuracy() -> Dict[str, Any]:
    """Generate prediction accuracy chart data."""
    # Generate accuracy for different prediction types
    categories = ['Temperature', 'Precipitation', 'Wind', 'Humidity', 'Pressure']
    
    # Accuracy for 1-day, 3-day, and 7-day predictions
    accuracy_1day = []
    accuracy_3day = []
    accuracy_7day = []
    
    for _ in categories:
        # 1-day predictions are most accurate
        accuracy_1day.append(round(random.uniform(90, 98), 1))
        
        # 3-day predictions are less accurate
        accuracy_3day.append(round(random.uniform(80, 90), 1))
        
        # 7-day predictions are least accurate
        accuracy_7day.append(round(random.uniform(70, 80), 1))
    
    return {
        'labels': categories,
        'datasets': [
            {
                'label': '1-Day Prediction',
                'data': accuracy_1day,
                'backgroundColor': 'rgba(33, 150, 243, 0.7)',
            },
            {
                'label': '3-Day Prediction',
                'data': accuracy_3day,
                'backgroundColor': 'rgba(76, 175, 80, 0.7)',
            },
            {
                'label': '7-Day Prediction',
                'data': accuracy_7day,
                'backgroundColor': 'rgba(255, 152, 0, 0.7)',
            }
        ]
    }


def _generate_device_contribution() -> Dict[str, Any]:
    """Generate device contribution chart data."""
    # Device types
    device_types = ['Desktop', 'Laptop', 'Mobile', 'Tablet', 'Server']
    
    # Contribution percentage
    contribution = [25, 30, 20, 10, 15]  # Must sum to 100
    
    # Colors
    colors = [
        'rgba(255, 99, 132, 0.7)',
        'rgba(54, 162, 235, 0.7)',
        'rgba(255, 206, 86, 0.7)',
        'rgba(75, 192, 192, 0.7)',
        'rgba(153, 102, 255, 0.7)'
    ]
    
    return {
        'labels': device_types,
        'datasets': [
            {
                'data': contribution,
                'backgroundColor': colors,
                'borderWidth': 1
            }
        ]
    }


def generate_map_data(map_type: str, location: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate map data for JavaScript visualization.
    
    Args:
        map_type: Type of map data to generate
        location: Optional location information
        
    Returns:
        Dict with map data in a format suitable for JavaScript maps
    """
    if map_type == 'temperature':
        return _generate_temperature_map(location)
    elif map_type == 'precipitation':
        return _generate_precipitation_map(location)
    elif map_type == 'wind':
        return _generate_wind_map(location)
    else:
        raise ValueError(f"Unknown map data type: {map_type}")


def _generate_temperature_map(location: Optional[Dict] = None) -> Dict[str, Any]:
    """Generate temperature map data."""
    # Default center if no location provided
    if not location:
        center = {'latitude': 43.6532, 'longitude': -79.3832}  # Toronto
    else:
        center = location
    
    # Generate points in a grid around the center
    points = []
    
    # Base temperature for the center
    base_temp = 20 + random.uniform(-5, 5)
    
    # Generate grid of points
    for lat_offset in range(-5, 6):
        for lon_offset in range(-5, 6):
            lat = center['latitude'] + (lat_offset * 0.1)
            lon = center['longitude'] + (lon_offset * 0.1)
            
            # Temperature varies with distance from center and some randomness
            distance = math.sqrt(lat_offset**2 + lon_offset**2)
            temp_variation = distance * random.uniform(-0.5, 0.5)
            
            temperature = base_temp + temp_variation
            
            points.append({
                'latitude': lat,
                'longitude': lon,
                'temperature': round(temperature, 1)
            })
    
    return {
        'center': center,
        'points': points
    }


def _generate_precipitation_map(location: Optional[Dict] = None) -> Dict[str, Any]:
    """Generate precipitation map data."""
    # Default center if no location provided
    if not location:
        center = {'latitude': 43.6532, 'longitude': -79.3832}  # Toronto
    else:
        center = location
    
    # Generate points in a grid around the center
    points = []
    
    # Generate a few rain cells
    rain_cells = []
    for _ in range(3):
        rain_cells.append({
            'latitude': center['latitude'] + random.uniform(-0.5, 0.5),
            'longitude': center['longitude'] + random.uniform(-0.5, 0.5),
            'intensity': random.uniform(0.5, 1.0)
        })
    
    # Generate grid of points
    for lat_offset in range(-5, 6):
        for lon_offset in range(-5, 6):
            lat = center['latitude'] + (lat_offset * 0.1)
            lon = center['longitude'] + (lon_offset * 0.1)
            
            # Precipitation varies with distance from rain cells
            precipitation = 0
            
            for cell in rain_cells:
                distance = math.sqrt(
                    (lat - cell['latitude'])**2 + 
                    (lon - cell['longitude'])**2
                )
                
                # Precipitation decreases with distance from cell
                if distance < 0.5:
                    cell_precip = (0.5 - distance) * cell['intensity'] * 10
                    precipitation += cell_precip
            
            # Add some randomness
            precipitation += random.uniform(-0.5, 0.5)
            precipitation = max(0, precipitation)
            
            points.append({
                'latitude': lat,
                'longitude': lon,
                'precipitation': round(precipitation, 1)
            })
    
    return {
        'center': center,
        'points': points
    }


def _generate_wind_map(location: Optional[Dict] = None) -> Dict[str, Any]:
    """Generate wind map data."""
    # Default center if no location provided
    if not location:
        center = {'latitude': 43.6532, 'longitude': -79.3832}  # Toronto
    else:
        center = location
    
    # Generate points in a grid around the center
    points = []
    
    # Base wind direction and speed
    base_direction = random.randint(0, 359)
    base_speed = random.uniform(5, 15)
    
    # Generate grid of points
    for lat_offset in range(-5, 6):
        for lon_offset in range(-5, 6):
            lat = center['latitude'] + (lat_offset * 0.1)
            lon = center['longitude'] + (lon_offset * 0.1)
            
            # Wind varies with position and some randomness
            direction_variation = random.uniform(-20, 20)
            speed_variation = random.uniform(-3, 3)
            
            direction = (base_direction + direction_variation) % 360
            speed = max(0, base_speed + speed_variation)
            
            points.append({
                'latitude': lat,
                'longitude': lon,
                'direction': round(direction, 1),
                'speed': round(speed, 1)
            })
    
    return {
        'center': center,
        'points': points
    }
