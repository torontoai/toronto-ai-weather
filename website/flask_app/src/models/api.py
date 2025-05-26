"""
API models for Toronto AI Weather web application.
"""

from datetime import datetime
import secrets
from src.main import db

class ApiKey(db.Model):
    """API key model for external access."""
    
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    key = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    
    # Relationships
    usage = db.relationship('ApiUsage', backref='api_key', lazy='dynamic')
    
    def __init__(self, user_id, name, description=None, expires_at=None):
        self.user_id = user_id
        self.key = self.generate_key()
        self.name = name
        self.description = description
        self.expires_at = expires_at
    
    @staticmethod
    def generate_key():
        """Generate a secure API key."""
        return secrets.token_hex(32)
    
    def is_expired(self):
        """Check if the API key is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if the API key is valid."""
        return self.is_active and not self.is_expired()
    
    def update_last_used(self):
        """Update the last used timestamp."""
        self.last_used = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<ApiKey {self.name}>'

class ApiUsage(db.Model):
    """Model for tracking API usage."""
    
    __tablename__ = 'api_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'))
    endpoint = db.Column(db.String(120))
    method = db.Column(db.String(10))
    status_code = db.Column(db.Integer)
    response_time = db.Column(db.Float)  # in milliseconds
    request_size = db.Column(db.Integer)  # in bytes
    response_size = db.Column(db.Integer)  # in bytes
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ApiUsage {self.endpoint} at {self.timestamp}>'

class ApiQuota(db.Model):
    """Model for API usage quotas."""
    
    __tablename__ = 'api_quotas'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tier = db.Column(db.String(20))
    daily_limit = db.Column(db.Integer)
    monthly_limit = db.Column(db.Integer)
    current_daily_usage = db.Column(db.Integer, default=0)
    current_monthly_usage = db.Column(db.Integer, default=0)
    reset_day = db.Column(db.Integer)  # Day of month for monthly reset
    last_daily_reset = db.Column(db.DateTime)
    last_monthly_reset = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ApiQuota {self.user_id} - {self.tier}>'
    
    def increment_usage(self):
        """Increment usage counters."""
        self.current_daily_usage += 1
        self.current_monthly_usage += 1
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def check_quota(self):
        """Check if quota is exceeded."""
        # Check if resets are needed
        now = datetime.utcnow()
        
        # Daily reset
        if self.last_daily_reset:
            days_since_reset = (now - self.last_daily_reset).days
            if days_since_reset >= 1:
                self.current_daily_usage = 0
                self.last_daily_reset = now
        else:
            self.last_daily_reset = now
        
        # Monthly reset
        if self.last_monthly_reset:
            if now.day == self.reset_day and now.month != self.last_monthly_reset.month:
                self.current_monthly_usage = 0
                self.last_monthly_reset = now
        else:
            self.last_monthly_reset = now
        
        # Check limits
        daily_exceeded = self.daily_limit > 0 and self.current_daily_usage >= self.daily_limit
        monthly_exceeded = self.monthly_limit > 0 and self.current_monthly_usage >= self.monthly_limit
        
        return not (daily_exceeded or monthly_exceeded)
