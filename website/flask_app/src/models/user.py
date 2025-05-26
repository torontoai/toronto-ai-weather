"""
User model for Toronto AI Weather.

This module provides the User model for authentication and authorization.
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from src.main import db

class User(db.Model, UserMixin):
    """User model for authentication and authorization."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role = db.Column(db.String(20), default='civilian')  # civilian, agency, government, military
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)
    
    # Relationships
    devices = db.relationship('Device', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == 'admin'
    
    def is_military(self):
        """Check if user is military."""
        return self.role == 'military'
    
    def is_government(self):
        """Check if user is government."""
        return self.role == 'government'
    
    def is_agency(self):
        """Check if user is from a weather/news agency."""
        return self.role == 'agency'
    
    def is_civilian(self):
        """Check if user is a civilian."""
        return self.role == 'civilian'
    
    def __repr__(self):
        return f'<User {self.username}>'
