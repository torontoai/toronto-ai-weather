"""
Pure Python weather data utilities for Toronto AI Weather.

This module provides weather data utilities using only pure Python
without any native dependencies like numpy or pandas.
"""

import json
import random
import math
import datetime
import requests
from typing import Dict, List, Any, Optional, Tuple, Union


class WeatherData:
    """Class for handling weather data without native dependencies."""
    
    def __init__(self):
        """Initialize the weather data handler."""
        self.cache = {}
        self.last_update = {}
    
    def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get current weather for a location using web API.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            Dict with weather data
        """
        # Check cache first (5 minute validity)
        cache_key = f"{latitude:.2f}_{longitude:.2f}"
        now = datetime.datetime.now()
        
        if cache_key in self.cache and cache_key in self.last_update:
            time_diff = (now - self.last_update[cache_key]).total_seconds()
            if time_diff < 300:  # 5 minutes
                return self.cache[cache_key]
        
        # For demo purposes, generate realistic weather data
        # In production, this would call a weather API
        weather = self._generate_weather_data(latitude, longitude)
        
        # Update cache
        self.cache[cache_key] = weather
        self.last_update[cache_key] = now
        
        return weather
    
    def get_forecast(self, latitude: float, longitude: float, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get weather forecast for a location using web API.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            hours: Number of hours to forecast
            
        Returns:
            List of dicts with forecast data
        """
        # For demo purposes, generate realistic forecast data
        # In production, this would call a weather API
        forecast = []
        
        # Get current weather as starting point
        current = self.get_current_weather(latitude, longitude)
        
        # Generate hourly forecast
        now = datetime.datetime.now()
        
        for i in range(hours):
            forecast_time = now + datetime.timedelta(hours=i)
            
            # Temperature varies with time of day
            hour_of_day = forecast_time.hour
            diurnal_variation = self._get_diurnal_variation(hour_of_day)
            
            # Add some randomness but maintain trend
            temp_trend = random.uniform(-0.5, 0.5)  # Overall trend direction
            random_variation = random.uniform(-1.0, 1.0)
            
            # Calculate new temperature
            new_temp = current['temperature'] + temp_trend + random_variation + diurnal_variation
            
            # Occasionally change weather condition
            if random.random() > 0.8:
                conditions = ["Clear", "Partly Cloudy", "Cloudy", "Overcast", 
                             "Light Rain", "Rain", "Heavy Rain", 
                             "Light Snow", "Snow", "Heavy Snow",
                             "Thunderstorm", "Fog", "Mist"]
                new_condition = random.choice(conditions)
            else:
                new_condition = current['condition']
            
            # Create forecast entry
            forecast.append({
                'timestamp': forecast_time.isoformat(),
                'temperature': round(new_temp, 1),
                'condition': new_condition,
                'humidity': round(random.uniform(30, 90), 1),
                'wind_speed': round(random.uniform(0, 30), 1),
                'wind_direction': random.randint(0, 359),
                'precipitation_probability': round(random.uniform(0, 1), 2),
                'confidence': round(0.9 - (i * 0.01), 2)  # Confidence decreases with time
            })
        
        return forecast
    
    def _generate_weather_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Generate realistic weather data based on location."""
        # Determine season based on current date
        now = datetime.datetime.now()
        month = now.month
        
        # Adjust for hemisphere (summer in northern is winter in southern)
        is_northern = latitude >= 0
        
        # Determine season factor (-1 to 1, where 1 is peak summer, -1 is peak winter)
        if is_northern:
            # Northern hemisphere: Summer peaks in July (month 7)
            season_factor = math.cos((month - 7) * math.pi / 6)
        else:
            # Southern hemisphere: Summer peaks in January (month 1)
            season_factor = math.cos((month - 1) * math.pi / 6)
        
        # Base temperature varies with latitude (equator is warmest)
        equator_max_temp = 30  # Celsius
        pole_max_temp = -20  # Celsius
        
        # Linear interpolation between equator and pole temperatures based on latitude
        latitude_factor = abs(latitude) / 90
        max_temp = equator_max_temp - (equator_max_temp - pole_max_temp) * latitude_factor
        
        # Adjust for season
        seasonal_variation = 20  # Celsius, difference between summer and winter
        temp = max_temp - (seasonal_variation * (1 - season_factor)) / 2
        
        # Add some randomness
        temp += random.uniform(-5, 5)
        
        # Determine weather condition based on temperature and randomness
        if temp < -10:
            conditions = ["Snow", "Heavy Snow", "Blizzard", "Clear"]
            weights = [0.4, 0.3, 0.2, 0.1]
        elif temp < 0:
            conditions = ["Snow", "Light Snow", "Cloudy", "Clear"]
            weights = [0.3, 0.3, 0.3, 0.1]
        elif temp < 10:
            conditions = ["Cloudy", "Partly Cloudy", "Light Rain", "Clear"]
            weights = [0.3, 0.3, 0.2, 0.2]
        elif temp < 20:
            conditions = ["Clear", "Partly Cloudy", "Cloudy", "Light Rain"]
            weights = [0.4, 0.3, 0.2, 0.1]
        else:
            conditions = ["Clear", "Partly Cloudy", "Thunderstorm", "Rain"]
            weights = [0.5, 0.3, 0.1, 0.1]
        
        # Normalize weights
        total = sum(weights)
        weights = [w/total for w in weights]
        
        # Select condition based on weights
        condition = random.choices(conditions, weights=weights, k=1)[0]
        
        # Generate other weather attributes
        humidity = random.uniform(30, 90)
        wind_speed = random.uniform(0, 30)
        wind_direction = random.randint(0, 359)
        pressure = random.uniform(990, 1030)
        
        return {
            'temperature': round(temp, 1),
            'condition': condition,
            'humidity': round(humidity, 1),
            'wind_speed': round(wind_speed, 1),
            'wind_direction': wind_direction,
            'pressure': round(pressure, 1),
            'timestamp': now.isoformat()
        }
    
    def _get_diurnal_variation(self, hour: int) -> float:
        """Calculate temperature variation based on time of day."""
        # Temperature typically peaks around 2-3 PM (hour 14-15) and bottoms out around 4-5 AM (hour 4-5)
        # Using a sinusoidal pattern with peak at hour 14
        return 3 * math.sin(math.pi * (hour - 4) / 12)


# Singleton instance
weather_data = WeatherData()


def get_current_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Get current weather for a location.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        
    Returns:
        Dict with weather data
    """
    return weather_data.get_current_weather(latitude, longitude)


def get_forecast(latitude: float, longitude: float, hours: int = 24) -> List[Dict[str, Any]]:
    """
    Get weather forecast for a location.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        hours: Number of hours to forecast
        
    Returns:
        List of dicts with forecast data
    """
    return weather_data.get_forecast(latitude, longitude, hours)


def get_historical_data(latitude: float, longitude: float, days: int = 7) -> List[Dict[str, Any]]:
    """
    Get historical weather data for a location.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        days: Number of days of historical data
        
    Returns:
        List of dicts with historical data
    """
    # For demo purposes, generate realistic historical data
    # In production, this would call a weather API or database
    historical = []
    
    # Get current weather as reference point
    current = weather_data.get_current_weather(latitude, longitude)
    
    # Generate daily historical data
    now = datetime.datetime.now()
    
    for i in range(days, 0, -1):
        historical_time = now - datetime.timedelta(days=i)
        
        # Temperature varies with day
        day_variation = random.uniform(-5, 5)
        
        # Calculate historical temperature
        hist_temp = current['temperature'] + day_variation
        
        # Generate weather condition
        conditions = ["Clear", "Partly Cloudy", "Cloudy", "Overcast", 
                     "Light Rain", "Rain", "Heavy Rain", 
                     "Light Snow", "Snow", "Heavy Snow",
                     "Thunderstorm", "Fog", "Mist"]
        hist_condition = random.choice(conditions)
        
        # Create historical entry
        historical.append({
            'date': historical_time.date().isoformat(),
            'temperature_high': round(hist_temp + random.uniform(2, 5), 1),
            'temperature_low': round(hist_temp - random.uniform(2, 5), 1),
            'condition': hist_condition,
            'humidity': round(random.uniform(30, 90), 1),
            'wind_speed': round(random.uniform(0, 30), 1),
            'precipitation': round(random.uniform(0, 20), 1),
        })
    
    return historical
