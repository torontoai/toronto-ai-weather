"""
Device models for Toronto AI Weather web application.
"""

from datetime import datetime
from src.main import db

class Device(db.Model):
    """Device model for distributed computation."""
    
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    device_uuid = db.Column(db.String(64), unique=True, index=True)
    device_name = db.Column(db.String(64))
    device_type = db.Column(db.String(20))  # desktop, mobile, tablet, server
    os_name = db.Column(db.String(64))
    os_version = db.Column(db.String(64))
    browser_name = db.Column(db.String(64))
    browser_version = db.Column(db.String(64))
    cpu_cores = db.Column(db.Integer)
    cpu_speed = db.Column(db.Float)
    memory_total = db.Column(db.Float)  # in MB
    gpu_name = db.Column(db.String(64))
    gpu_memory = db.Column(db.Float)  # in MB
    network_type = db.Column(db.String(20))  # wifi, cellular, ethernet
    network_speed = db.Column(db.Float)  # in Mbps
    max_resource_allocation = db.Column(db.Float)  # percentage (0-1)
    is_active = db.Column(db.Boolean, default=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    contributions = db.relationship('DeviceContribution', backref='device', lazy='dynamic')
    
    def __repr__(self):
        return f'<Device {self.device_uuid}>'
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_uuid': self.device_uuid,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'os_name': self.os_name,
            'os_version': self.os_version,
            'browser_name': self.browser_name,
            'browser_version': self.browser_version,
            'cpu_cores': self.cpu_cores,
            'cpu_speed': self.cpu_speed,
            'memory_total': self.memory_total,
            'gpu_name': self.gpu_name,
            'gpu_memory': self.gpu_memory,
            'network_type': self.network_type,
            'network_speed': self.network_speed,
            'max_resource_allocation': self.max_resource_allocation,
            'is_active': self.is_active,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat()
        }

class DeviceContribution(db.Model):
    """Model for tracking device contributions to the system."""
    
    __tablename__ = 'device_contributions'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'))
    task_id = db.Column(db.String(64))
    task_type = db.Column(db.String(64))
    cpu_usage = db.Column(db.Float)  # percentage (0-1)
    memory_usage = db.Column(db.Float)  # in MB
    gpu_usage = db.Column(db.Float)  # percentage (0-1)
    network_usage = db.Column(db.Float)  # in MB
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # in seconds
    status = db.Column(db.String(20))  # completed, failed, cancelled
    result_quality = db.Column(db.Float)  # percentage (0-1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DeviceContribution {self.device_id} - {self.task_id}>'
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'task_id': self.task_id,
            'task_type': self.task_type,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'gpu_usage': self.gpu_usage,
            'network_usage': self.network_usage,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'status': self.status,
            'result_quality': self.result_quality,
            'created_at': self.created_at.isoformat()
        }

class ComputationTask(db.Model):
    """Model for distributed computation tasks."""
    
    __tablename__ = 'computation_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_uuid = db.Column(db.String(64), unique=True, index=True)
    task_type = db.Column(db.String(64))
    priority = db.Column(db.Integer)
    status = db.Column(db.String(20))  # queued, assigned, processing, completed, failed
    data = db.Column(db.Text)  # JSON data
    result = db.Column(db.Text)  # JSON result
    required_resources = db.Column(db.Text)  # JSON resource requirements
    assigned_to = db.Column(db.Integer, db.ForeignKey('devices.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<ComputationTask {self.task_uuid}>'
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'task_uuid': self.task_uuid,
            'task_type': self.task_type,
            'priority': self.priority,
            'status': self.status,
            'data': self.data,
            'result': self.result,
            'required_resources': self.required_resources,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class SystemMetrics(db.Model):
    """Model for tracking system-wide metrics."""
    
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    active_devices = db.Column(db.Integer)
    total_cpu_power = db.Column(db.Float)  # in GHz
    total_memory = db.Column(db.Float)  # in GB
    total_gpu_power = db.Column(db.Float)  # in TFLOPS
    active_tasks = db.Column(db.Integer)
    completed_tasks = db.Column(db.Integer)
    failed_tasks = db.Column(db.Integer)
    average_task_duration = db.Column(db.Float)  # in seconds
    average_prediction_accuracy = db.Column(db.Float)  # percentage (0-1)
    system_load = db.Column(db.Float)  # percentage (0-1)
    
    def __repr__(self):
        return f'<SystemMetrics at {self.timestamp}>'
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'active_devices': self.active_devices,
            'total_cpu_power': self.total_cpu_power,
            'total_memory': self.total_memory,
            'total_gpu_power': self.total_gpu_power,
            'active_tasks': self.active_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'average_task_duration': self.average_task_duration,
            'average_prediction_accuracy': self.average_prediction_accuracy,
            'system_load': self.system_load
        }
