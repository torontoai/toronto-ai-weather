"""
Device model for Toronto AI Weather.

This module provides the Device model for tracking connected devices
and their contributions to the distributed computation network.
"""

from datetime import datetime
from src.main import db

class Device(db.Model):
    """Device model for tracking connected devices and their contributions."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    device_id = db.Column(db.String(64), unique=True, nullable=False)
    device_type = db.Column(db.String(20))  # desktop, laptop, mobile, tablet, server
    os_type = db.Column(db.String(20))
    browser_type = db.Column(db.String(20))
    ip_address = db.Column(db.String(45))
    last_connected = db.Column(db.DateTime, default=datetime.utcnow)
    first_connected = db.Column(db.DateTime, default=datetime.utcnow)
    total_computation_time = db.Column(db.Integer, default=0)  # in seconds
    total_tasks_completed = db.Column(db.Integer, default=0)
    performance_score = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    
    def update_connection(self):
        """Update last connected time."""
        self.last_connected = datetime.utcnow()
    
    def add_computation_time(self, seconds):
        """Add computation time to device."""
        self.total_computation_time += seconds
    
    def add_task(self):
        """Increment tasks completed."""
        self.total_tasks_completed += 1
    
    def update_performance_score(self, score):
        """Update performance score."""
        # Weighted average (30% new score, 70% existing score)
        if self.performance_score == 0.0:
            self.performance_score = score
        else:
            self.performance_score = (0.3 * score) + (0.7 * self.performance_score)
    
    def get_contribution_level(self):
        """Get contribution level based on device type and performance."""
        base_levels = {
            'server': 10.0,
            'desktop': 5.0,
            'laptop': 3.0,
            'tablet': 1.0,
            'mobile': 0.5
        }
        
        base = base_levels.get(self.device_type, 1.0)
        return base * (self.performance_score / 100)
    
    def __repr__(self):
        return f'<Device {self.device_id}>'
