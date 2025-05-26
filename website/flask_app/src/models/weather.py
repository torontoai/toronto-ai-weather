"""
Weather data models for Toronto AI Weather web application.
"""

from datetime import datetime
from src.main import db

class Location(db.Model):
    """Location model for weather data."""
    
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    country = db.Column(db.String(64))
    region = db.Column(db.String(64))
    city = db.Column(db.String(64))
    timezone = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    weather_data = db.relationship('WeatherData', backref='location', lazy='dynamic')
    forecasts = db.relationship('Forecast', backref='location', lazy='dynamic')
    
    def __repr__(self):
        return f'<Location {self.name} ({self.latitude}, {self.longitude})>'

class WeatherData(db.Model):
    """Current weather data model."""
    
    __tablename__ = 'weather_data'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    temperature = db.Column(db.Float)
    feels_like = db.Column(db.Float)
    humidity = db.Column(db.Float)
    pressure = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Float)
    weather_condition = db.Column(db.String(64))
    weather_description = db.Column(db.String(120))
    weather_icon = db.Column(db.String(20))
    cloud_coverage = db.Column(db.Float)
    visibility = db.Column(db.Float)
    uv_index = db.Column(db.Float)
    precipitation = db.Column(db.Float)
    dew_point = db.Column(db.Float)
    source = db.Column(db.String(64))
    accuracy = db.Column(db.Float)
    
    def __repr__(self):
        return f'<WeatherData {self.location_id} at {self.timestamp}>'
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'location_id': self.location_id,
            'timestamp': self.timestamp.isoformat(),
            'temperature': self.temperature,
            'feels_like': self.feels_like,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'weather_condition': self.weather_condition,
            'weather_description': self.weather_description,
            'weather_icon': self.weather_icon,
            'cloud_coverage': self.cloud_coverage,
            'visibility': self.visibility,
            'uv_index': self.uv_index,
            'precipitation': self.precipitation,
            'dew_point': self.dew_point,
            'source': self.source,
            'accuracy': self.accuracy
        }

class Forecast(db.Model):
    """Weather forecast model."""
    
    __tablename__ = 'forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    prediction_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    forecast_timestamp = db.Column(db.DateTime)
    temperature = db.Column(db.Float)
    feels_like = db.Column(db.Float)
    humidity = db.Column(db.Float)
    pressure = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Float)
    weather_condition = db.Column(db.String(64))
    weather_description = db.Column(db.String(120))
    weather_icon = db.Column(db.String(20))
    cloud_coverage = db.Column(db.Float)
    visibility = db.Column(db.Float)
    uv_index = db.Column(db.Float)
    precipitation_probability = db.Column(db.Float)
    precipitation_amount = db.Column(db.Float)
    dew_point = db.Column(db.Float)
    confidence = db.Column(db.Float)
    model_version = db.Column(db.String(64))
    
    def __repr__(self):
        return f'<Forecast {self.location_id} for {self.forecast_timestamp}>'
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'location_id': self.location_id,
            'prediction_timestamp': self.prediction_timestamp.isoformat(),
            'forecast_timestamp': self.forecast_timestamp.isoformat(),
            'temperature': self.temperature,
            'feels_like': self.feels_like,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'weather_condition': self.weather_condition,
            'weather_description': self.weather_description,
            'weather_icon': self.weather_icon,
            'cloud_coverage': self.cloud_coverage,
            'visibility': self.visibility,
            'uv_index': self.uv_index,
            'precipitation_probability': self.precipitation_probability,
            'precipitation_amount': self.precipitation_amount,
            'dew_point': self.dew_point,
            'confidence': self.confidence,
            'model_version': self.model_version
        }

class WeatherAlert(db.Model):
    """Weather alert model."""
    
    __tablename__ = 'weather_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    alert_type = db.Column(db.String(64))
    severity = db.Column(db.String(20))
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    issuing_authority = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WeatherAlert {self.alert_type} for {self.location_id}>'

class PredictionAccuracy(db.Model):
    """Model for tracking prediction accuracy."""
    
    __tablename__ = 'prediction_accuracy'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    forecast_id = db.Column(db.Integer, db.ForeignKey('forecasts.id'))
    actual_weather_id = db.Column(db.Integer, db.ForeignKey('weather_data.id'))
    temperature_error = db.Column(db.Float)
    humidity_error = db.Column(db.Float)
    pressure_error = db.Column(db.Float)
    wind_speed_error = db.Column(db.Float)
    wind_direction_error = db.Column(db.Float)
    precipitation_error = db.Column(db.Float)
    condition_matched = db.Column(db.Boolean)
    overall_accuracy = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PredictionAccuracy {self.forecast_id} vs {self.actual_weather_id}>'
