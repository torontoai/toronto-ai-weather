"""
Utility functions for distributed computation.
"""

import json
import uuid
from datetime import datetime
import logging

from src.main import db
from src.models.device import Device, ComputationTask, DeviceContribution, SystemMetrics

logger = logging.getLogger(__name__)

def register_device_task(device):
    """
    Register a device with the distributed computation system.
    
    Args:
        device: Device object
        
    Returns:
        bool: Success status
    """
    try:
        # Update system metrics
        update_system_metrics()
        
        # In a real implementation, this would register the device with a task scheduler
        logger.info(f"Device registered: {device.device_uuid}")
        
        return True
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        return False

def submit_computation_task(task_type, priority, data, required_resources, user_id=None):
    """
    Submit a task to the distributed computation system.
    
    Args:
        task_type (str): Type of task
        priority (int): Task priority (1-10)
        data (dict): Task data
        required_resources (dict): Required resources
        user_id (int): User ID
        
    Returns:
        ComputationTask: Created task
    """
    try:
        # Create task
        task = ComputationTask(
            task_uuid=str(uuid.uuid4()),
            task_type=task_type,
            priority=priority,
            status='queued',
            data=json.dumps(data),
            required_resources=json.dumps(required_resources)
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Assign task to device
        assign_task_to_device(task)
        
        return task
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        db.session.rollback()
        raise

def assign_task_to_device(task):
    """
    Assign a task to an available device.
    
    Args:
        task: ComputationTask object
        
    Returns:
        bool: Success status
    """
    try:
        # Find available devices
        devices = Device.query.filter_by(is_active=True).all()
        
        if not devices:
            logger.warning("No active devices available for task assignment")
            return False
        
        # In a real implementation, this would use a sophisticated matching algorithm
        # For now, just assign to the first device
        device = devices[0]
        
        task.status = 'assigned'
        task.assigned_to = device.id
        db.session.commit()
        
        logger.info(f"Task {task.task_uuid} assigned to device {device.device_uuid}")
        
        return True
    except Exception as e:
        logger.error(f"Error assigning task: {e}")
        db.session.rollback()
        return False

def update_system_metrics():
    """
    Update system-wide metrics.
    
    Returns:
        SystemMetrics: Updated metrics
    """
    try:
        # Count active devices
        active_devices = Device.query.filter_by(is_active=True).count()
        
        # Calculate total CPU power
        total_cpu_power = db.session.query(
            db.func.sum(Device.cpu_cores * Device.cpu_speed)
        ).filter_by(is_active=True).scalar() or 0.0
        
        # Calculate total memory
        total_memory = db.session.query(
            db.func.sum(Device.memory_total)
        ).filter_by(is_active=True).scalar() or 0.0
        
        # Convert to GB
        total_memory = total_memory / 1024.0
        
        # Calculate total GPU power (placeholder)
        total_gpu_power = 0.0
        
        # Count active tasks
        active_tasks = ComputationTask.query.filter(
            ComputationTask.status.in_(['queued', 'assigned', 'processing'])
        ).count()
        
        # Count completed tasks
        completed_tasks = ComputationTask.query.filter_by(
            status='completed'
        ).count()
        
        # Count failed tasks
        failed_tasks = ComputationTask.query.filter_by(
            status='failed'
        ).count()
        
        # Calculate average task duration
        avg_duration = db.session.query(
            db.func.avg(DeviceContribution.duration)
        ).scalar() or 0.0
        
        # Calculate average prediction accuracy
        from src.models.weather import PredictionAccuracy
        avg_accuracy = db.session.query(
            db.func.avg(PredictionAccuracy.overall_accuracy)
        ).scalar() or 0.0
        
        # Calculate system load
        system_load = 0.7  # Placeholder value
        
        # Create metrics
        metrics = SystemMetrics(
            active_devices=active_devices,
            total_cpu_power=total_cpu_power,
            total_memory=total_memory,
            total_gpu_power=total_gpu_power,
            active_tasks=active_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            average_task_duration=avg_duration,
            average_prediction_accuracy=avg_accuracy,
            system_load=system_load
        )
        
        db.session.add(metrics)
        db.session.commit()
        
        return metrics
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")
        db.session.rollback()
        return None

def get_device_contribution_stats(device_id):
    """
    Get contribution statistics for a device.
    
    Args:
        device_id: Device ID
        
    Returns:
        dict: Contribution statistics
    """
    try:
        # Get device
        device = Device.query.get(device_id)
        
        if not device:
            return None
        
        # Get contributions
        contributions = DeviceContribution.query.filter_by(
            device_id=device_id
        ).all()
        
        # Calculate statistics
        total_tasks = len(contributions)
        completed_tasks = sum(1 for c in contributions if c.status == 'completed')
        failed_tasks = sum(1 for c in contributions if c.status == 'failed')
        total_duration = sum(c.duration for c in contributions if c.duration)
        avg_duration = total_duration / total_tasks if total_tasks > 0 else 0
        
        # Calculate resource usage
        avg_cpu_usage = sum(c.cpu_usage for c in contributions if c.cpu_usage) / total_tasks if total_tasks > 0 else 0
        avg_memory_usage = sum(c.memory_usage for c in contributions if c.memory_usage) / total_tasks if total_tasks > 0 else 0
        avg_gpu_usage = sum(c.gpu_usage for c in contributions if c.gpu_usage) / total_tasks if total_tasks > 0 else 0
        
        # Calculate quality
        avg_quality = sum(c.result_quality for c in contributions if c.result_quality) / completed_tasks if completed_tasks > 0 else 0
        
        return {
            'device': device,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'total_duration': total_duration,
            'avg_duration': avg_duration,
            'avg_cpu_usage': avg_cpu_usage,
            'avg_memory_usage': avg_memory_usage,
            'avg_gpu_usage': avg_gpu_usage,
            'avg_quality': avg_quality
        }
    except Exception as e:
        logger.error(f"Error getting device contribution stats: {e}")
        return None

def get_task_distribution_stats():
    """
    Get task distribution statistics.
    
    Returns:
        dict: Task distribution statistics
    """
    try:
        # Get task counts by type
        task_types = db.session.query(
            ComputationTask.task_type, db.func.count(ComputationTask.id)
        ).group_by(ComputationTask.task_type).all()
        
        # Get task counts by status
        task_statuses = db.session.query(
            ComputationTask.status, db.func.count(ComputationTask.id)
        ).group_by(ComputationTask.status).all()
        
        # Get task counts by priority
        task_priorities = db.session.query(
            ComputationTask.priority, db.func.count(ComputationTask.id)
        ).group_by(ComputationTask.priority).all()
        
        return {
            'task_types': dict(task_types),
            'task_statuses': dict(task_statuses),
            'task_priorities': dict(task_priorities)
        }
    except Exception as e:
        logger.error(f"Error getting task distribution stats: {e}")
        return None
