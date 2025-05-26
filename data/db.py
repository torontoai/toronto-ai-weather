"""
Database connection and models for Toronto AI Weather.
"""

import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

from toronto_ai_weather.config.config import DATABASE

# Set up logging
logger = logging.getLogger(__name__)

# Create database URL
DB_URL = f"postgresql://{DATABASE['user']}:{DATABASE['password']}@{DATABASE['host']}:{DATABASE['port']}/{DATABASE['name']}"

# Create engine
try:
    engine = create_engine(DB_URL)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Error creating database engine: {e}")
    raise

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Define models
class WeatherData(Base):
    """Model for storing weather data from various sources."""
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    location = Column(String(100), nullable=False, index=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    """Model for user information."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(100), nullable=False)
    group = Column(String(20), nullable=False, index=True)  # civilian, enterprise, military
    totp_secret = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Prediction(Base):
    """Model for weather predictions."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    location = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    prediction_type = Column(String(50), nullable=False, index=True)  # temperature, precipitation, etc.
    prediction_data = Column(JSON, nullable=False)
    accuracy = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ExpertFeedback(Base):
    """Model for storing feedback from meteorologists and experts."""
    __tablename__ = "expert_feedback"

    id = Column(Integer, primary_key=True, index=True)
    expert_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    feedback_text = Column(Text, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    is_incorporated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    expert = relationship("User")
    prediction = relationship("Prediction")

class ModelPerformance(Base):
    """Model for tracking ML model performance."""
    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50), nullable=False, index=True)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class ComputationContribution(Base):
    """Model for tracking user contributions to distributed computation."""
    __tablename__ = "computation_contributions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_type = Column(String(50), nullable=False)
    computation_time = Column(Float, nullable=False)  # in seconds
    points_earned = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User")

def init_db():
    """Initialize the database by creating all tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Create hypertable for time-series data
def create_hypertables():
    """Create hypertables for time-series data."""
    try:
        with engine.connect() as conn:
            # Create hypertable for weather_data
            conn.execute("SELECT create_hypertable('weather_data', 'timestamp', if_not_exists => TRUE);")
            # Create hypertable for predictions
            conn.execute("SELECT create_hypertable('predictions', 'timestamp', if_not_exists => TRUE);")
            # Create hypertable for model_performance
            conn.execute("SELECT create_hypertable('model_performance', 'timestamp', if_not_exists => TRUE);")
            # Create hypertable for computation_contributions
            conn.execute("SELECT create_hypertable('computation_contributions', 'timestamp', if_not_exists => TRUE);")
            logger.info("Hypertables created successfully")
    except Exception as e:
        logger.error(f"Error creating hypertables: {e}")
        raise
