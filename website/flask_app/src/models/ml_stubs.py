"""
ML model stubs for Toronto AI Weather.

This module provides stub implementations of the machine learning models
that would normally be powered by TensorFlow. These stubs return realistic
mock data for demonstration purposes.
"""

import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
import json
import os


class WeatherPredictionModelStub:
    """Stub implementation of the weather prediction model."""
    
    def __init__(self):
        """Initialize the stub model."""
        self.name = "Weather Prediction Model Stub"
        self.version = "1.0.0"
        self.is_stub = True
        
        # Load sample data if available
        sample_data_path = os.path.join(os.path.dirname(__file__), 'sample_data', 'weather_samples.json')
        self.sample_data = {}
        
        try:
            if os.path.exists(sample_data_path):
                with open(sample_data_path, 'r') as f:
                    self.sample_data = json.load(f)
        except Exception:
            # If sample data can't be loaded, we'll generate random data
            pass
    
    def predict_temperature(self, location, timestamp, historical_data=None):
        """
        Predict temperature for a given location and time.
        
        Args:
            location: Dict with 'latitude' and 'longitude'
            timestamp: Datetime object for the prediction time
            historical_data: Optional historical data to base prediction on
            
        Returns:
            Dict with prediction results
        """
        # Generate realistic temperature based on latitude and season
        base_temp = self._get_base_temperature(location['latitude'], timestamp)
        
        # Add some randomness
        variation = random.uniform(-3.0, 3.0)
        predicted_temp = base_temp + variation
        
        # Calculate confidence based on how much historical data we have
        confidence = 0.85 + random.uniform(-0.1, 0.1)
        if historical_data is not None and len(historical_data) > 0:
            confidence += min(0.1, len(historical_data) * 0.01)
        
        return {
            'temperature': round(predicted_temp, 1),
            'confidence': round(min(0.98, confidence), 2),
            'prediction_time': datetime.now().isoformat(),
            'model_version': self.version
        }
    
    def predict_weather_conditions(self, location, timestamp, historical_data=None):
        """
        Predict weather conditions for a given location and time.
        
        Args:
            location: Dict with 'latitude' and 'longitude'
            timestamp: Datetime object for the prediction time
            historical_data: Optional historical data to base prediction on
            
        Returns:
            Dict with prediction results
        """
        # List of possible weather conditions
        conditions = [
            "Clear", "Partly Cloudy", "Cloudy", "Overcast", 
            "Light Rain", "Rain", "Heavy Rain", 
            "Light Snow", "Snow", "Heavy Snow",
            "Thunderstorm", "Fog", "Mist"
        ]
        
        # Get season and latitude to influence probability
        month = timestamp.month
        lat = location['latitude']
        
        # Adjust probabilities based on season and latitude
        if abs(lat) > 60:  # Polar regions
            if month in [12, 1, 2]:  # Winter
                weights = [0.2, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05, 0.1, 0.15, 0.1, 0, 0.05, 0.05]
            else:  # Summer
                weights = [0.3, 0.2, 0.15, 0.1, 0.05, 0.05, 0.05, 0.05, 0, 0, 0, 0.05, 0]
        elif abs(lat) > 30:  # Temperate regions
            if month in [12, 1, 2]:  # Winter
                weights = [0.15, 0.15, 0.2, 0.15, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0, 0]
            else:  # Summer
                weights = [0.3, 0.2, 0.1, 0.05, 0.1, 0.05, 0.05, 0, 0, 0, 0.1, 0.05, 0]
        else:  # Tropical regions
            if month in [6, 7, 8]:  # Rainy season
                weights = [0.1, 0.1, 0.15, 0.15, 0.15, 0.15, 0.1, 0, 0, 0, 0.1, 0, 0]
            else:  # Dry season
                weights = [0.4, 0.3, 0.1, 0.05, 0.05, 0.05, 0, 0, 0, 0, 0.05, 0, 0]
        
        # Normalize weights
        total = sum(weights)
        weights = [w/total for w in weights]
        
        # Select condition based on weights
        condition = random.choices(conditions, weights=weights, k=1)[0]
        
        # Calculate confidence
        confidence = 0.8 + random.uniform(-0.1, 0.1)
        if historical_data is not None and len(historical_data) > 0:
            confidence += min(0.15, len(historical_data) * 0.01)
        
        return {
            'condition': condition,
            'confidence': round(min(0.98, confidence), 2),
            'prediction_time': datetime.now().isoformat(),
            'model_version': self.version
        }
    
    def predict_full_forecast(self, location, start_time, hours=24):
        """
        Generate a full weather forecast for a location over a time period.
        
        Args:
            location: Dict with 'latitude' and 'longitude'
            start_time: Datetime object for the start of the forecast
            hours: Number of hours to forecast
            
        Returns:
            List of hourly forecast dictionaries
        """
        forecast = []
        
        # Generate base temperature and conditions
        base_temp = self._get_base_temperature(location['latitude'], start_time)
        base_condition = self.predict_weather_conditions(location, start_time)['condition']
        
        # Generate hourly variations with some continuity
        temp_trend = random.uniform(-0.5, 0.5)  # Overall trend direction
        condition_stability = random.uniform(0.7, 0.9)  # How stable the conditions are
        
        current_temp = base_temp
        current_condition = base_condition
        
        for hour in range(hours):
            timestamp = start_time + timedelta(hours=hour)
            
            # Temperature varies with time of day
            hour_of_day = timestamp.hour
            diurnal_variation = self._get_diurnal_variation(hour_of_day)
            
            # Add some randomness but maintain trend
            random_variation = random.uniform(-1.0, 1.0)
            current_temp += temp_trend * 0.1 + random_variation * 0.2 + diurnal_variation
            
            # Occasionally change weather condition
            if random.random() > condition_stability:
                new_condition = self.predict_weather_conditions(location, timestamp)['condition']
                current_condition = new_condition
            
            # Create forecast entry
            forecast.append({
                'timestamp': timestamp.isoformat(),
                'temperature': round(current_temp, 1),
                'condition': current_condition,
                'humidity': round(random.uniform(30, 90), 1),
                'wind_speed': round(random.uniform(0, 30), 1),
                'wind_direction': random.randint(0, 359),
                'precipitation_probability': round(random.uniform(0, 1), 2),
                'confidence': round(0.9 - (hour * 0.01), 2)  # Confidence decreases with time
            })
        
        return forecast
    
    def _get_base_temperature(self, latitude, timestamp):
        """Calculate a realistic base temperature based on latitude and season."""
        # Adjust for hemisphere (summer in northern is winter in southern)
        month = timestamp.month
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
        
        return temp
    
    def _get_diurnal_variation(self, hour):
        """Calculate temperature variation based on time of day."""
        # Temperature typically peaks around 2-3 PM (hour 14-15) and bottoms out around 4-5 AM (hour 4-5)
        # Using a sinusoidal pattern with peak at hour 14
        return 3 * math.sin(math.pi * (hour - 4) / 12)


class AnomalyDetectionModelStub:
    """Stub implementation of the anomaly detection model."""
    
    def __init__(self):
        """Initialize the stub model."""
        self.name = "Anomaly Detection Model Stub"
        self.version = "1.0.0"
        self.is_stub = True
        
        # Anomaly types and their probabilities
        self.anomaly_types = {
            "temperature_spike": 0.3,
            "pressure_drop": 0.2,
            "unusual_wind_pattern": 0.15,
            "precipitation_anomaly": 0.25,
            "humidity_anomaly": 0.1
        }
    
    def detect_anomalies(self, data, location=None, timestamp=None):
        """
        Detect weather anomalies in the provided data.
        
        Args:
            data: Weather data to analyze
            location: Optional location information
            timestamp: Optional timestamp
            
        Returns:
            Dict with anomaly detection results
        """
        # Randomly decide if there's an anomaly (20% chance)
        has_anomaly = random.random() < 0.2
        
        if not has_anomaly:
            return {
                'anomalies_detected': 0,
                'anomalies': [],
                'analysis_time': datetime.now().isoformat(),
                'model_version': self.version,
                'confidence': 0.95
            }
        
        # Determine how many anomalies (usually 1, occasionally 2)
        num_anomalies = 1 if random.random() < 0.8 else 2
        
        # Generate anomalies
        anomalies = []
        for _ in range(num_anomalies):
            # Select anomaly type based on probabilities
            anomaly_type = random.choices(
                list(self.anomaly_types.keys()),
                weights=list(self.anomaly_types.values()),
                k=1
            )[0]
            
            # Generate anomaly details
            anomaly = {
                'type': anomaly_type,
                'severity': round(random.uniform(0.6, 0.95), 2),
                'detected_at': datetime.now().isoformat(),
                'confidence': round(random.uniform(0.7, 0.95), 2)
            }
            
            # Add location-specific details if provided
            if location:
                anomaly['location'] = location
            
            # Add timestamp if provided
            if timestamp:
                anomaly['timestamp'] = timestamp.isoformat()
            
            anomalies.append(anomaly)
        
        return {
            'anomalies_detected': len(anomalies),
            'anomalies': anomalies,
            'analysis_time': datetime.now().isoformat(),
            'model_version': self.version,
            'confidence': round(random.uniform(0.85, 0.98), 2)
        }


# Add missing math module import
import math


# Factory function to get model instances
def get_model(model_type):
    """
    Get a model instance based on type.
    
    Args:
        model_type: String identifier for the model type
        
    Returns:
        Model instance
    """
    if model_type == 'weather_prediction':
        return WeatherPredictionModelStub()
    elif model_type == 'anomaly_detection':
        return AnomalyDetectionModelStub()
    else:
        raise ValueError(f"Unknown model type: {model_type}")
