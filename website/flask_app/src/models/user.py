"""
User model for Toronto AI Weather web application.
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from src.main import db

class UserTier:
    """User access tiers."""
    CIVILIAN = 'civilian'
    WEATHER_AGENCY = 'weather_agency'
    NEWS = 'news'
    GOVERNMENT = 'government'
    MILITARY = 'military'
    ADMIN = 'admin'

class User(UserMixin, db.Model):
    """User model for authentication and access control."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    tier = db.Column(db.String(20), default=UserTier.CIVILIAN)
    organization = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    devices = db.relationship('Device', backref='user', lazy='dynamic')
    api_keys = db.relationship('ApiKey', backref='user', lazy='dynamic')
    locations = db.relationship('SavedLocation', backref='user', lazy='dynamic')
    
    def __init__(self, username, email, password, tier=UserTier.CIVILIAN, 
                 first_name=None, last_name=None, organization=None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.tier = tier
        self.first_name = first_name
        self.last_name = last_name
        self.organization = organization
        
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
        return self.tier == UserTier.ADMIN
    
    def is_higher_tier(self):
        """Check if user has higher than civilian access."""
        return self.tier != UserTier.CIVILIAN
    
    def can_access_api(self):
        """Check if user can access API."""
        return self.tier in [UserTier.WEATHER_AGENCY, UserTier.NEWS, 
                            UserTier.GOVERNMENT, UserTier.MILITARY, 
                            UserTier.ADMIN]
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'

class SavedLocation(db.Model):
    """Saved locations for users."""
    
    __tablename__ = 'saved_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(64))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SavedLocation {self.name}>'

class RegistrationRequest(db.Model):
    """Registration requests for higher tier access."""
    
    __tablename__ = 'registration_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, index=True)
    organization = db.Column(db.String(120))
    requested_tier = db.Column(db.String(20))
    justification = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<RegistrationRequest {self.email} - {self.requested_tier}>'
