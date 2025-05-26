"""
Configuration settings for Toronto AI Weather application.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database settings
DATABASE = {
    'engine': 'timescaledb',
    'name': 'toronto_ai_weather',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432,
}

# Redis settings
REDIS = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
}

# Kafka settings
KAFKA = {
    'bootstrap_servers': 'localhost:9092',
    'topics': {
        'military': 'toronto-ai-weather-military',
        'enterprise': 'toronto-ai-weather-enterprise',
        'civilian': 'toronto-ai-weather-civilian',
    }
}

# API settings
API = {
    'host': '0.0.0.0',
    'port': 8000,
    'debug': True,
    'reload': True,
}

# Security settings
SECURITY = {
    'secret_key': os.environ.get('SECRET_KEY', 'toronto-ai-weather-secret-key'),
    'algorithm': 'HS256',
    'access_token_expire_minutes': 30,
}

# Data sources
DATA_SOURCES = {
    'weather_stations': {
        'noaa': {
            'api_url': 'https://api.weather.gov/stations',
            'update_interval': 3600,  # seconds
        },
        'eccc': {
            'api_url': 'https://dd.weather.gc.ca/citypage_weather/xml',
            'update_interval': 3600,  # seconds
        },
    },
    'satellite': {
        'nasa': {
            'api_url': 'https://api.nasa.gov/planetary/earth/imagery',
            'api_key': os.environ.get('NASA_API_KEY', ''),
            'update_interval': 86400,  # seconds
        },
    },
    'social_media': {
        'twitter': {
            'api_url': 'https://api.twitter.com/2/tweets/search/recent',
            'api_key': os.environ.get('TWITTER_API_KEY', ''),
            'api_secret': os.environ.get('TWITTER_API_SECRET', ''),
            'update_interval': 300,  # seconds
        },
    },
}

# Model settings
MODEL = {
    'base_dir': BASE_DIR / 'models',
    'version': '0.1.0',
    'batch_size': 64,
    'epochs': 100,
    'learning_rate': 0.001,
    'validation_split': 0.2,
}

# Logging settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'toronto_ai_weather.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
