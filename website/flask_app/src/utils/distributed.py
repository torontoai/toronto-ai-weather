"""
Distributed computation utilities for Toronto AI Weather.

This module provides utilities for managing distributed computation
across connected devices using pure Python (no native dependencies).
"""

import json
import random
import datetime
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union

from src.main import db
from src.models.device import Device

def register_device(user_id: int, device_type: str, os_type: str, 
                   browser_type: str, ip_address: str) -> str:
    """
    Register a device for distributed computation.
    
    Args:
        user_id: User ID
        device_type: Type of device (desktop, laptop, mobile, tablet, server)
        os_type: Operating system
        browser_type: Browser type
        ip_address: IP address
        
    Returns:
        Device ID
    """
    # Generate unique device ID
    device_id = str(uuid.uuid4())
    
    # Check if device already exists with this IP for this user
    existing_device = Device.query.filter_by(
        user_id=user_id,
        ip_address=ip_address,
        device_type=device_type,
        browser_type=browser_type
    ).first()
    
    if existing_device:
        # Update existing device
        existing_device.update_connection()
        db.session.commit()
        return existing_device.device_id
    
    # Create new device
    device = Device(
        user_id=user_id,
        device_id=device_id,
        device_type=device_type,
        os_type=os_type,
        browser_type=browser_type,
        ip_address=ip_address
    )
    
    db.session.add(device)
    db.session.commit()
    
    return device_id

def get_device_stats(user_id: int) -> Dict[str, Any]:
    """
    Get statistics for a user's devices.
    
    Args:
        user_id: User ID
        
    Returns:
        Dict with device statistics
    """
    devices = Device.query.filter_by(user_id=user_id).all()
    
    if not devices:
        return {
            'device_count': 0,
            'total_computation_time': 0,
            'total_tasks_completed': 0,
            'average_performance': 0.0,
            'contribution_level': 0.0
        }
    
    total_computation_time = sum(d.total_computation_time for d in devices)
    total_tasks_completed = sum(d.total_tasks_completed for d in devices)
    average_performance = sum(d.performance_score for d in devices) / len(devices)
    contribution_level = sum(d.get_contribution_level() for d in devices)
    
    return {
        'device_count': len(devices),
        'total_computation_time': total_computation_time,
        'total_tasks_completed': total_tasks_completed,
        'average_performance': round(average_performance, 2),
        'contribution_level': round(contribution_level, 2)
    }

def assign_task(device_id: str) -> Dict[str, Any]:
    """
    Assign a computation task to a device.
    
    Args:
        device_id: Device ID
        
    Returns:
        Dict with task details
    """
    # Get device
    device = Device.query.filter_by(device_id=device_id).first()
    
    if not device:
        return {
            'task_id': None,
            'error': 'Device not found'
        }
    
    # Update device connection time
    device.update_connection()
    db.session.commit()
    
    # Task types based on device capabilities
    task_types = {
        'server': ['data_processing', 'model_training', 'prediction', 'anomaly_detection'],
        'desktop': ['data_processing', 'prediction', 'anomaly_detection'],
        'laptop': ['data_processing', 'prediction'],
        'tablet': ['data_collection', 'simple_prediction'],
        'mobile': ['data_collection']
    }
    
    # Get appropriate task types for this device
    device_task_types = task_types.get(device.device_type, ['data_collection'])
    
    # Generate a task
    task_type = random.choice(device_task_types)
    task_id = str(uuid.uuid4())
    
    # Task difficulty based on device performance
    difficulty = min(1.0, device.performance_score / 100)
    
    # Generate task parameters based on type
    if task_type == 'data_processing':
        task_params = {
            'data_points': int(100 + (900 * difficulty)),
            'processing_type': random.choice(['filtering', 'aggregation', 'normalization']),
            'region': random.choice(['north_america', 'europe', 'asia', 'africa', 'south_america', 'oceania'])
        }
    elif task_type == 'model_training':
        task_params = {
            'model_type': random.choice(['temperature', 'precipitation', 'wind', 'pressure']),
            'iterations': int(10 + (90 * difficulty)),
            'learning_rate': 0.01 + (0.09 * random.random())
        }
    elif task_type == 'prediction':
        task_params = {
            'prediction_type': random.choice(['temperature', 'precipitation', 'wind', 'pressure']),
            'location': {
                'latitude': random.uniform(-90, 90),
                'longitude': random.uniform(-180, 180)
            },
            'hours_ahead': random.randint(1, 72)
        }
    elif task_type == 'anomaly_detection':
        task_params = {
            'data_type': random.choice(['temperature', 'precipitation', 'wind', 'pressure']),
            'threshold': 0.7 + (0.2 * random.random()),
            'window_size': random.randint(6, 24)
        }
    elif task_type == 'simple_prediction':
        task_params = {
            'prediction_type': random.choice(['temperature', 'precipitation']),
            'location': {
                'latitude': random.uniform(-90, 90),
                'longitude': random.uniform(-180, 180)
            },
            'hours_ahead': random.randint(1, 24)
        }
    else:  # data_collection
        task_params = {
            'data_type': random.choice(['temperature', 'precipitation', 'wind', 'pressure']),
            'frequency': random.randint(1, 10),
            'duration': random.randint(5, 30)
        }
    
    # Estimated completion time (in seconds)
    estimated_time = int(10 + (50 * difficulty))
    
    return {
        'task_id': task_id,
        'task_type': task_type,
        'parameters': task_params,
        'estimated_time': estimated_time,
        'deadline': (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat()
    }

def process_task_result(device_id: str, task_id: str, result: Dict[str, Any]) -> bool:
    """
    Process the result of a computation task.
    
    Args:
        device_id: Device ID
        task_id: Task ID
        result: Task result data
        
    Returns:
        Success flag
    """
    # Get device
    device = Device.query.filter_by(device_id=device_id).first()
    
    if not device:
        return False
    
    # Update device stats
    device.add_task()
    
    # Add computation time
    if 'computation_time' in result:
        device.add_computation_time(result['computation_time'])
    
    # Update performance score
    if 'performance_score' in result:
        device.update_performance_score(result['performance_score'])
    
    db.session.commit()
    
    return True

def get_system_stats() -> Dict[str, Any]:
    """
    Get overall system statistics.
    
    Returns:
        Dict with system statistics
    """
    # Count active devices (connected in the last hour)
    one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
    active_devices = Device.query.filter(Device.last_connected >= one_hour_ago).count()
    
    # Total devices
    total_devices = Device.query.count()
    
    # Total computation time
    total_computation_time = db.session.query(db.func.sum(Device.total_computation_time)).scalar() or 0
    
    # Total tasks completed
    total_tasks_completed = db.session.query(db.func.sum(Device.total_tasks_completed)).scalar() or 0
    
    # Average performance score
    avg_performance = db.session.query(db.func.avg(Device.performance_score)).scalar() or 0.0
    
    # Device type distribution
    device_types = db.session.query(
        Device.device_type, 
        db.func.count(Device.id)
    ).group_by(Device.device_type).all()
    
    device_distribution = {device_type: count for device_type, count in device_types}
    
    return {
        'active_devices': active_devices,
        'total_devices': total_devices,
        'total_computation_time': total_computation_time,
        'total_tasks_completed': total_tasks_completed,
        'average_performance': round(avg_performance, 2),
        'device_distribution': device_distribution
    }
