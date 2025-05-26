"""
Main API module for Toronto AI Weather.

This module defines the FastAPI application and routes.
"""

import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from toronto_ai_weather.api.auth import (
    Token, UserCreate, UserInDB, authenticate_user, create_user, 
    get_current_user, update_last_login, verify_totp, create_access_token
)
from toronto_ai_weather.data.db import get_db, User, Prediction
from toronto_ai_weather.config.config import API

# Set up logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Toronto AI Weather API",
    description="API for Toronto AI Weather prediction system",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Toronto AI Weather API"}

# Authentication routes
@app.post("/auth/register", response_model=UserInDB)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    return create_user(db, user)

@app.post("/auth/login", response_model=Token)
async def login(username: str, password: str, totp_code: str = None, db: Session = Depends(get_db)):
    """Login and get access token."""
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check TOTP for military users
    if user.group == "military":
        if not totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TOTP code required for military users",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_totp(user, totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid TOTP code",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Update last login
    update_last_login(db, user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "group": user.group}
    )
    
    return {"access_token": access_token, "token_type": "bearer", "group": user.group}

# Weather prediction routes
@app.get("/weather/current")
async def get_current_weather(location: str = "toronto", user: User = Depends(get_current_user)):
    """Get current weather for a location."""
    # This would normally fetch real data, but for now return mock data
    return {
        "location": location,
        "timestamp": "2025-05-26T04:45:00Z",
        "temperature": 22.5,
        "humidity": 65,
        "wind_speed": 10,
        "wind_direction": "NW",
        "conditions": "Partly Cloudy",
    }

@app.get("/weather/forecast")
async def get_weather_forecast(
    location: str = "toronto", 
    days: int = 5,
    user: User = Depends(get_current_user)
):
    """Get weather forecast for a location."""
    # This would normally fetch real forecast data, but for now return mock data
    forecast = []
    for i in range(days):
        forecast.append({
            "date": f"2025-05-{26 + i}",
            "temperature_high": 22 + i,
            "temperature_low": 15 + i,
            "precipitation_chance": 30 - (i * 5),
            "conditions": "Partly Cloudy",
        })
    
    return {
        "location": location,
        "forecast": forecast,
    }

# Military-specific routes
@app.get("/military/anomalies")
async def get_weather_anomalies(user: User = Depends(get_current_user)):
    """Get weather anomalies (military users only)."""
    if user.group != "military":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Military clearance required.",
        )
    
    # This would normally fetch real anomaly data, but for now return mock data
    return {
        "anomalies": [
            {
                "location": "Lake Ontario",
                "timestamp": "2025-05-26T02:30:00Z",
                "type": "Unusual Pressure Drop",
                "severity": "Medium",
                "description": "Sudden barometric pressure drop not aligned with weather patterns",
            },
            {
                "location": "Northern Toronto",
                "timestamp": "2025-05-26T03:15:00Z",
                "type": "Electromagnetic Anomaly",
                "severity": "Low",
                "description": "Brief spike in electromagnetic readings",
            },
        ]
    }

# Enterprise-specific routes
@app.get("/enterprise/analytics")
async def get_weather_analytics(user: User = Depends(get_current_user)):
    """Get weather analytics (enterprise users only)."""
    if user.group not in ["enterprise", "military"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Enterprise subscription required.",
        )
    
    # This would normally fetch real analytics data, but for now return mock data
    return {
        "analytics": {
            "temperature_trend": "Rising",
            "precipitation_forecast": "Below Average",
            "seasonal_comparison": "2.3°C above last year",
            "impact_analysis": {
                "agriculture": "Moderate stress on crops due to higher temperatures",
                "energy": "15% increase in cooling demand expected",
                "transportation": "No significant impact expected",
            },
        }
    }

# User contribution routes
@app.get("/user/contributions")
async def get_user_contributions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's contributions to distributed computation."""
    # This would normally fetch real contribution data, but for now return mock data
    return {
        "total_points": 1250,
        "computation_time": 3600,  # seconds
        "tasks_completed": 42,
        "rank": 15,
    }

def start_app():
    """Start the FastAPI application."""
    import uvicorn
    uvicorn.run(
        "toronto_ai_weather.api.main:app",
        host=API['host'],
        port=API['port'],
        reload=API['reload'],
    )

if __name__ == "__main__":
    start_app()
