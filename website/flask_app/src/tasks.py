"""
Background tasks for Toronto AI Weather application.
"""

from celery import shared_task
import logging
from datetime import datetime, timedelta

from src.main import db
from src.models.device import SystemMetrics, ComputationTask, DeviceContribution
from src.models.weather import WeatherData, Forecast, PredictionAccuracy
from src.utils.distributed import update_system_metrics
from src.utils.weather import get_current_weather, get_forecast

logger = logging.getLogger(__name__)

@shared_task
def update_system_metrics_task():
    """Update system-wide metrics."""
    try:
        metrics = update_system_metrics()
        return {
            'status': 'success',
            'active_devices': metrics.active_devices,
            'system_load': metrics.system_load
        }
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

@shared_task
def process_weather_data_task():
    """Process new weather data."""
    try:
        # Get locations that need updating
        locations = db.session.query(
            db.func.distinct(WeatherData.location_id)
        ).all()
        
        location_ids = [loc[0] for loc in locations]
        
        processed_count = 0
        
        for location_id in location_ids:
            # Get location
            from src.models.weather import Location
            location = Location.query.get(location_id)
            
            if not location:
                continue
            
            # Get current weather
            weather = get_current_weather(location.latitude, location.longitude)
            
            if weather:
                processed_count += 1
        
        return {
            'status': 'success',
            'processed_locations': processed_count
        }
    except Exception as e:
        logger.error(f"Error processing weather data: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

@shared_task
def update_predictions_task():
    """Update weather predictions."""
    try:
        # Get locations that need updating
        locations = db.session.query(
            db.func.distinct(WeatherData.location_id)
        ).all()
        
        location_ids = [loc[0] for loc in locations]
        
        updated_count = 0
        
        for location_id in location_ids:
            # Get location
            from src.models.weather import Location
            location = Location.query.get(location_id)
            
            if not location:
                continue
            
            # Get forecast
            forecasts = get_forecast(location.latitude, location.longitude, hours=24)
            
            if forecasts:
                updated_count += 1
        
        return {
            'status': 'success',
            'updated_locations': updated_count
        }
    except Exception as e:
        logger.error(f"Error updating predictions: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

@shared_task
def cleanup_old_tasks_task():
    """Clean up old tasks and contributions."""
    try:
        # Delete tasks older than 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        old_tasks = ComputationTask.query.filter(
            ComputationTask.created_at < thirty_days_ago
        ).all()
        
        for task in old_tasks:
            db.session.delete(task)
        
        # Delete contributions older than 30 days
        old_contributions = DeviceContribution.query.filter(
            DeviceContribution.created_at < thirty_days_ago
        ).all()
        
        for contribution in old_contributions:
            db.session.delete(contribution)
        
        # Commit changes
        db.session.commit()
        
        return {
            'status': 'success',
            'deleted_tasks': len(old_tasks),
            'deleted_contributions': len(old_contributions)
        }
    except Exception as e:
        logger.error(f"Error cleaning up old tasks: {e}")
        db.session.rollback()
        return {
            'status': 'error',
            'message': str(e)
        }

@shared_task
def calculate_prediction_accuracy_task():
    """Calculate prediction accuracy."""
    try:
        # Get forecasts from yesterday
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        forecasts = Forecast.query.filter(
            Forecast.created_at >= yesterday.replace(hour=0, minute=0, second=0),
            Forecast.created_at <= yesterday.replace(hour=23, minute=59, second=59)
        ).all()
        
        # Group by location
        forecast_by_location = {}
        
        for forecast in forecasts:
            if forecast.location_id not in forecast_by_location:
                forecast_by_location[forecast.location_id] = []
            
            forecast_by_location[forecast.location_id].append(forecast)
        
        # Calculate accuracy for each location
        accuracy_records = []
        
        for location_id, location_forecasts in forecast_by_location.items():
            # Get actual weather data
            actual_weather = WeatherData.query.filter(
                WeatherData.location_id == location_id,
                WeatherData.timestamp >= yesterday.replace(hour=0, minute=0, second=0),
                WeatherData.timestamp <= yesterday.replace(hour=23, minute=59, second=59)
            ).all()
            
            # Create mapping of timestamp to actual weather
            actual_by_time = {}
            
            for weather in actual_weather:
                # Round to nearest hour
                hour = weather.timestamp.replace(minute=0, second=0, microsecond=0)
                actual_by_time[hour] = weather
            
            # Calculate accuracy for each forecast
            temp_accuracy = []
            condition_accuracy = []
            
            for forecast in location_forecasts:
                # Find closest actual weather
                forecast_time = forecast.forecast_timestamp
                
                if forecast_time in actual_by_time:
                    actual = actual_by_time[forecast_time]
                    
                    # Calculate temperature accuracy
                    temp_diff = abs(forecast.temperature - actual.temperature)
                    temp_acc = max(0, 1 - (temp_diff / 10))  # 10°C difference = 0% accuracy
                    temp_accuracy.append(temp_acc)
                    
                    # Calculate condition accuracy
                    condition_acc = 1.0 if forecast.weather_condition == actual.weather_condition else 0.0
                    condition_accuracy.append(condition_acc)
            
            # Calculate overall accuracy
            if temp_accuracy and condition_accuracy:
                avg_temp_acc = sum(temp_accuracy) / len(temp_accuracy)
                avg_condition_acc = sum(condition_accuracy) / len(condition_accuracy)
                
                overall_acc = (avg_temp_acc * 0.7) + (avg_condition_acc * 0.3)
                
                # Create accuracy record
                accuracy = PredictionAccuracy(
                    location_id=location_id,
                    date=yesterday.date(),
                    temperature_accuracy=avg_temp_acc,
                    condition_accuracy=avg_condition_acc,
                    overall_accuracy=overall_acc
                )
                
                db.session.add(accuracy)
                accuracy_records.append(accuracy)
        
        # Commit changes
        db.session.commit()
        
        return {
            'status': 'success',
            'accuracy_records': len(accuracy_records)
        }
    except Exception as e:
        logger.error(f"Error calculating prediction accuracy: {e}")
        db.session.rollback()
        return {
            'status': 'error',
            'message': str(e)
        }

# Map task names to functions
task_map = {
    'update_system_metrics': update_system_metrics_task,
    'process_weather_data': process_weather_data_task,
    'update_predictions': update_predictions_task,
    'cleanup_old_tasks': cleanup_old_tasks_task,
    'calculate_prediction_accuracy': calculate_prediction_accuracy_task
}
