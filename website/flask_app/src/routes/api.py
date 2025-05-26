"""
API routes for Toronto AI Weather web application.
"""

from flask import Blueprint, request, jsonify, g
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime

from src.main import db
from src.models.user import User, UserTier
from src.models.weather import Location, WeatherData, Forecast, WeatherAlert
from src.models.device import Device, DeviceContribution, ComputationTask, SystemMetrics
from src.models.api import ApiKey, ApiUsage, ApiQuota
from src.utils.weather import get_current_weather, get_forecast
from src.utils.distributed import register_device_task, submit_computation_task

api_bp = Blueprint('api', __name__)

def require_api_key(f):
    """Decorator to require API key for access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 401
        
        key = ApiKey.query.filter_by(key=api_key).first()
        
        if not key:
            return jsonify({'error': 'Invalid API key'}), 401
        
        if not key.is_valid():
            return jsonify({'error': 'API key is expired or inactive'}), 401
        
        # Check quota
        quota = ApiQuota.query.filter_by(user_id=key.user_id).first()
        if quota and not quota.check_quota():
            return jsonify({'error': 'API quota exceeded'}), 429
        
        # Store API key for later use
        g.api_key = key
        g.user = User.query.get(key.user_id)
        
        # Update last used timestamp
        key.update_last_used()
        
        # Log API usage
        usage = ApiUsage(
            api_key_id=key.id,
            endpoint=request.path,
            method=request.method,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(usage)
        
        # Increment quota usage if applicable
        if quota:
            quota.increment_usage()
        
        db.session.commit()
        
        return f(*args, **kwargs)
    return decorated_function

def require_tier(tier_level):
    """Decorator to require specific user tier for access."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # If using API key authentication
            if hasattr(g, 'user'):
                user = g.user
            # If using session authentication
            elif current_user.is_authenticated:
                user = current_user
            else:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check tier level
            tier_levels = {
                UserTier.CIVILIAN: 0,
                UserTier.WEATHER_AGENCY: 1,
                UserTier.NEWS: 1,
                UserTier.GOVERNMENT: 2,
                UserTier.MILITARY: 3,
                UserTier.ADMIN: 4
            }
            
            user_level = tier_levels.get(user.tier, 0)
            required_level = tier_levels.get(tier_level, 0)
            
            if user_level < required_level:
                return jsonify({'error': 'Insufficient access level'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@api_bp.route('/weather/current')
@require_api_key
def current_weather():
    """Get current weather for a location."""
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

@api_bp.route('/weather/forecast')
@require_api_key
def forecast():
    """Get weather forecast for a location."""
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

@api_bp.route('/weather/alerts')
@require_api_key
def alerts():
    """Get active weather alerts."""
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    
    if latitude and longitude:
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        # Get alerts for specific location
        location = Location.query.filter_by(
            latitude=latitude,
            longitude=longitude
        ).first()
        
        if location:
            alerts = WeatherAlert.query.filter_by(
                location_id=location.id
            ).filter(
                WeatherAlert.end_time > datetime.utcnow()
            ).all()
            
            return jsonify([{
                'id': a.id,
                'alert_type': a.alert_type,
                'severity': a.severity,
                'title': a.title,
                'description': a.description,
                'start_time': a.start_time.isoformat(),
                'end_time': a.end_time.isoformat(),
                'issuing_authority': a.issuing_authority
            } for a in alerts]), 200
        else:
            return jsonify([]), 200
    else:
        # Get all active alerts
        alerts = WeatherAlert.query.filter(
            WeatherAlert.end_time > datetime.utcnow()
        ).all()
        
        return jsonify([{
            'id': a.id,
            'location_id': a.location_id,
            'alert_type': a.alert_type,
            'severity': a.severity,
            'title': a.title,
            'description': a.description,
            'start_time': a.start_time.isoformat(),
            'end_time': a.end_time.isoformat(),
            'issuing_authority': a.issuing_authority
        } for a in alerts]), 200

@api_bp.route('/system/metrics')
@require_api_key
@require_tier(UserTier.WEATHER_AGENCY)
def system_metrics():
    """Get system metrics."""
    metrics = SystemMetrics.query.order_by(
        SystemMetrics.timestamp.desc()
    ).first()
    
    if metrics:
        return jsonify(metrics.to_dict()), 200
    else:
        return jsonify({'error': 'Metrics not available'}), 404

@api_bp.route('/system/accuracy')
@require_api_key
def accuracy():
    """Get prediction accuracy metrics."""
    from src.models.weather import PredictionAccuracy
    
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
    
    return jsonify({
        'overall_accuracy': overall_accuracy,
        'temperature_accuracy': temperature_accuracy,
        'humidity_accuracy': humidity_accuracy,
        'precipitation_accuracy': precipitation_accuracy,
        'accuracy_trend': [{
            'date': date.isoformat(),
            'accuracy': float(accuracy)
        } for date, accuracy in accuracy_trend]
    }), 200

@api_bp.route('/device/register', methods=['POST'])
@require_api_key
def register_device():
    """Register a device for distributed computation."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    
    required_fields = ['device_uuid', 'device_name', 'device_type', 'os_name', 
                      'os_version', 'cpu_cores', 'memory_total', 'max_resource_allocation']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Check if device already exists
    existing_device = Device.query.filter_by(
        device_uuid=data['device_uuid']
    ).first()
    
    if existing_device:
        # Update existing device
        existing_device.device_name = data['device_name']
        existing_device.device_type = data['device_type']
        existing_device.os_name = data['os_name']
        existing_device.os_version = data['os_version']
        existing_device.browser_name = data.get('browser_name')
        existing_device.browser_version = data.get('browser_version')
        existing_device.cpu_cores = data['cpu_cores']
        existing_device.cpu_speed = data.get('cpu_speed')
        existing_device.memory_total = data['memory_total']
        existing_device.gpu_name = data.get('gpu_name')
        existing_device.gpu_memory = data.get('gpu_memory')
        existing_device.network_type = data.get('network_type')
        existing_device.network_speed = data.get('network_speed')
        existing_device.max_resource_allocation = data['max_resource_allocation']
        existing_device.is_active = True
        existing_device.last_seen = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Device updated successfully',
            'device_id': existing_device.id
        }), 200
    
    # Create new device
    device = Device(
        user_id=g.user.id,
        device_uuid=data['device_uuid'],
        device_name=data['device_name'],
        device_type=data['device_type'],
        os_name=data['os_name'],
        os_version=data['os_version'],
        browser_name=data.get('browser_name'),
        browser_version=data.get('browser_version'),
        cpu_cores=data['cpu_cores'],
        cpu_speed=data.get('cpu_speed'),
        memory_total=data['memory_total'],
        gpu_name=data.get('gpu_name'),
        gpu_memory=data.get('gpu_memory'),
        network_type=data.get('network_type'),
        network_speed=data.get('network_speed'),
        max_resource_allocation=data['max_resource_allocation']
    )
    
    db.session.add(device)
    db.session.commit()
    
    # Register device with task system
    register_device_task(device)
    
    return jsonify({
        'message': 'Device registered successfully',
        'device_id': device.id
    }), 201

@api_bp.route('/device/heartbeat', methods=['POST'])
@require_api_key
def device_heartbeat():
    """Update device heartbeat."""
    data = request.get_json()
    
    if not data or 'device_uuid' not in data:
        return jsonify({'error': 'Device UUID is required'}), 400
    
    device = Device.query.filter_by(
        device_uuid=data['device_uuid']
    ).first()
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    # Update device status
    device.is_active = True
    device.last_seen = datetime.utcnow()
    
    # Update resource availability if provided
    if 'available_resources' in data:
        resources = data['available_resources']
        # This would be stored in a separate table in a real implementation
    
    db.session.commit()
    
    # Check for pending tasks
    tasks = ComputationTask.query.filter_by(
        assigned_to=device.id,
        status='assigned'
    ).all()
    
    return jsonify({
        'message': 'Heartbeat received',
        'pending_tasks': len(tasks),
        'tasks': [{
            'task_uuid': task.task_uuid,
            'task_type': task.task_type,
            'priority': task.priority,
            'data': task.data
        } for task in tasks]
    }), 200

@api_bp.route('/task/submit', methods=['POST'])
@require_api_key
@require_tier(UserTier.WEATHER_AGENCY)
def submit_task():
    """Submit a computation task."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    
    required_fields = ['task_type', 'priority', 'data', 'required_resources']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Submit task to distributed computation system
    task = submit_computation_task(
        task_type=data['task_type'],
        priority=data['priority'],
        data=data['data'],
        required_resources=data['required_resources'],
        user_id=g.user.id
    )
    
    return jsonify({
        'message': 'Task submitted successfully',
        'task_uuid': task.task_uuid
    }), 201

@api_bp.route('/task/result', methods=['POST'])
@require_api_key
def submit_task_result():
    """Submit a task result."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    
    required_fields = ['task_uuid', 'device_uuid', 'status', 'result']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Find the task
    task = ComputationTask.query.filter_by(
        task_uuid=data['task_uuid']
    ).first()
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Find the device
    device = Device.query.filter_by(
        device_uuid=data['device_uuid']
    ).first()
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    # Update task status
    task.status = data['status']
    task.result = data['result']
    task.completed_at = datetime.utcnow()
    
    # Record device contribution
    contribution = DeviceContribution(
        device_id=device.id,
        task_id=task.task_uuid,
        task_type=task.task_type,
        cpu_usage=data.get('cpu_usage', 0.0),
        memory_usage=data.get('memory_usage', 0.0),
        gpu_usage=data.get('gpu_usage', 0.0),
        network_usage=data.get('network_usage', 0.0),
        start_time=datetime.utcnow() - timedelta(seconds=data.get('duration', 0.0)),
        end_time=datetime.utcnow(),
        duration=data.get('duration', 0.0),
        status=data['status'],
        result_quality=data.get('result_quality', 1.0)
    )
    
    db.session.add(contribution)
    db.session.commit()
    
    return jsonify({
        'message': 'Task result submitted successfully'
    }), 200

@api_bp.route('/keys', methods=['GET'])
@login_required
def list_api_keys():
    """List user's API keys."""
    if not current_user.can_access_api():
        return jsonify({'error': 'You do not have API access'}), 403
    
    keys = ApiKey.query.filter_by(user_id=current_user.id).all()
    
    return jsonify([{
        'id': key.id,
        'name': key.name,
        'key': key.key,
        'description': key.description,
        'is_active': key.is_active,
        'expires_at': key.expires_at.isoformat() if key.expires_at else None,
        'created_at': key.created_at.isoformat(),
        'last_used': key.last_used.isoformat() if key.last_used else None
    } for key in keys]), 200

@api_bp.route('/keys', methods=['POST'])
@login_required
def create_api_key():
    """Create a new API key."""
    if not current_user.can_access_api():
        return jsonify({'error': 'You do not have API access'}), 403
    
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Key name is required'}), 400
    
    # Create new API key
    key = ApiKey(
        user_id=current_user.id,
        name=data['name'],
        description=data.get('description')
    )
    
    db.session.add(key)
    db.session.commit()
    
    return jsonify({
        'id': key.id,
        'name': key.name,
        'key': key.key,
        'description': key.description,
        'is_active': key.is_active,
        'expires_at': key.expires_at.isoformat() if key.expires_at else None,
        'created_at': key.created_at.isoformat()
    }), 201

@api_bp.route('/keys/<int:key_id>', methods=['DELETE'])
@login_required
def delete_api_key(key_id):
    """Delete an API key."""
    key = ApiKey.query.filter_by(
        id=key_id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(key)
    db.session.commit()
    
    return jsonify({'message': 'API key deleted successfully'}), 200
