"""
Celery worker configuration for Toronto AI Weather application.
"""

import os
from celery import Celery
from src.main import app

# Configure Celery
celery = Celery(
    'toronto_ai_weather',
    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
)

# Configure Celery to use the same settings as Flask app
celery.conf.update(app.config)

# Define periodic tasks
celery.conf.beat_schedule = {
    'update-system-metrics': {
        'task': 'src.tasks.update_system_metrics',
        'schedule': 60.0,  # Every minute
    },
    'process-weather-data': {
        'task': 'src.tasks.process_weather_data',
        'schedule': 300.0,  # Every 5 minutes
    },
    'update-predictions': {
        'task': 'src.tasks.update_predictions',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-tasks': {
        'task': 'src.tasks.cleanup_old_tasks',
        'schedule': 86400.0,  # Every day
    },
}

# Optional configuration
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Load tasks module
celery.autodiscover_tasks(['src.tasks'])
