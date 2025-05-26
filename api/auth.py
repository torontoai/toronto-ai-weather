"""
Authentication module for Toronto AI Weather.

This module handles user authentication, registration, and authorization.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import pyotp

from sqlalchemy.orm import Session
from toronto_ai_weather.data.db import User, get_db
from toronto_ai_weather.config.config import SECURITY

# Set up logging
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class Token(BaseModel):
    access_token: str
    token_type: str
    group: str

class TokenData(BaseModel):
    username: Optional[str] = None
    group: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    group: str = "civilian"  # Default to civilian

class UserInDB(BaseModel):
    id: int
    username: str
    email: str
    group: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=SECURITY['access_token_expire_minutes'])
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECURITY['secret_key'], algorithm=SECURITY['algorithm'])
    
    return encoded_jwt

def get_user(db: Session, username: str) -> Optional[User]:
    """Get a user by username."""
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user = get_user(db, username)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

def verify_totp(user: User, totp_code: str) -> bool:
    """Verify a TOTP code for a user."""
    if not user.totp_secret:
        return False
    
    totp = pyotp.TOTP(user.totp_secret)
    return totp.verify(totp_code)

def generate_totp_secret() -> str:
    """Generate a new TOTP secret."""
    return pyotp.random_base32()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get the current user from a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECURITY['secret_key'], algorithms=[SECURITY['algorithm']])
        username: str = payload.get("sub")
        group: str = payload.get("group")
        
        if username is None:
            raise credentials_exception
        
        token_data = TokenData(username=username, group=group)
    except JWTError:
        raise credentials_exception
    
    user = get_user(db, username=token_data.username)
    
    if user is None:
        raise credentials_exception
    
    return user

def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user."""
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        group=user.group,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    # Generate TOTP secret for military users
    if user.group == "military":
        db_user.totp_secret = generate_totp_secret()
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def update_last_login(db: Session, user: User) -> None:
    """Update the last login timestamp for a user."""
    user.last_login = datetime.utcnow()
    db.commit()
