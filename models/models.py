"""
Machine learning models for Toronto AI Weather.

This module contains the implementation of various machine learning models
for weather prediction and anomaly detection.
"""

import logging
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, LSTM, Conv1D, MaxPooling1D, Flatten, Input, Concatenate, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import os
import joblib

from toronto_ai_weather.config.config import MODEL

# Set up logging
logger = logging.getLogger(__name__)

class BaseModel:
    """Base class for all machine learning models."""
    
    def __init__(self, name: str, version: str = MODEL['version']):
        self.name = name
        self.version = version
        self.model = None
        self.scaler = None
        self.model_path = os.path.join(MODEL['base_dir'], f"{name}_{version}.h5")
        self.scaler_path = os.path.join(MODEL['base_dir'], f"{name}_{version}_scaler.pkl")
    
    def save(self) -> None:
        """Save the model and scaler to disk."""
        if self.model is not None:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Save model
            self.model.save(self.model_path)
            logger.info(f"Model saved to {self.model_path}")
            
            # Save scaler if it exists
            if self.scaler is not None:
                joblib.dump(self.scaler, self.scaler_path)
                logger.info(f"Scaler saved to {self.scaler_path}")
    
    def load(self) -> None:
        """Load the model and scaler from disk."""
        if os.path.exists(self.model_path):
            self.model = tf.keras.models.load_model(self.model_path)
            logger.info(f"Model loaded from {self.model_path}")
            
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info(f"Scaler loaded from {self.scaler_path}")
    
    def preprocess(self, data: pd.DataFrame) -> np.ndarray:
        """Preprocess data for model input."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def train(self, data: pd.DataFrame, target: pd.Series) -> Dict[str, Any]:
        """Train the model on the given data."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Make predictions using the trained model."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def evaluate(self, data: pd.DataFrame, target: pd.Series) -> Dict[str, float]:
        """Evaluate the model on the given data."""
        raise NotImplementedError("Subclasses must implement this method")


class TemperatureLSTM(BaseModel):
    """LSTM model for temperature prediction."""
    
    def __init__(self, version: str = MODEL['version'], sequence_length: int = 24):
        super().__init__(name="temperature_lstm", version=version)
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler(feature_range=(0, 1))
    
    def build_model(self, input_shape: Tuple[int, int]) -> None:
        """Build the LSTM model architecture."""
        self.model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        
        self.model.compile(
            optimizer=Adam(learning_rate=MODEL['learning_rate']),
            loss='mean_squared_error'
        )
        
        logger.info(f"Built LSTM model with input shape {input_shape}")
    
    def create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM input."""
        X, y = [], []
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(data[i + self.sequence_length, 0])  # Assuming temperature is the first column
        
        return np.array(X), np.array(y)
    
    def preprocess(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess data for LSTM model."""
        # Select relevant features (temperature and related features)
        features = data[['temperature', 'humidity', 'wind_speed']].values
        
        # Scale the features
        scaled_features = self.scaler.fit_transform(features)
        
        # Create sequences
        X, y = self.create_sequences(scaled_features)
        
        return X, y
    
    def train(self, data: pd.DataFrame, target: Optional[pd.Series] = None) -> Dict[str, Any]:
        """Train the LSTM model."""
        # Preprocess data
        X, y = self.preprocess(data)
        
        # Split into train and validation sets
        split_idx = int(len(X) * (1 - MODEL['validation_split']))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Build model if not already built
        if self.model is None:
            self.build_model(input_shape=(X_train.shape[1], X_train.shape[2]))
        
        # Set up callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ModelCheckpoint(self.model_path, save_best_only=True)
        ]
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            epochs=MODEL['epochs'],
            batch_size=MODEL['batch_size'],
            validation_data=(X_val, y_val),
            callbacks=callbacks,
            verbose=1
        )
        
        # Save model and scaler
        self.save()
        
        return {
            "history": history.history,
            "final_train_loss": history.history['loss'][-1],
            "final_val_loss": history.history['val_loss'][-1]
        }
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Make temperature predictions."""
        # Ensure model is loaded
        if self.model is None:
            self.load()
            if self.model is None:
                raise ValueError("Model not found. Please train the model first.")
        
        # Preprocess data
        X, _ = self.preprocess(data)
        
        # Make predictions
        scaled_predictions = self.model.predict(X)
        
        # Inverse transform to get actual temperature values
        # Create a dummy array with the right shape for inverse_transform
        dummy = np.zeros((len(scaled_predictions), 3))
        dummy[:, 0] = scaled_predictions.flatten()
        
        # Inverse transform
        predictions = self.scaler.inverse_transform(dummy)[:, 0]
        
        return predictions
    
    def evaluate(self, data: pd.DataFrame, target: pd.Series) -> Dict[str, float]:
        """Evaluate the model on test data."""
        # Make predictions
        predictions = self.predict(data)
        
        # Calculate metrics
        mse = mean_squared_error(target, predictions)
        mae = mean_absolute_error(target, predictions)
        rmse = np.sqrt(mse)
        
        return {
            "mse": mse,
            "mae": mae,
            "rmse": rmse
        }


class HybridCNNLSTM(BaseModel):
    """Hybrid CNN-LSTM model for spatial-temporal weather forecasting."""
    
    def __init__(self, version: str = MODEL['version'], sequence_length: int = 24):
        super().__init__(name="hybrid_cnn_lstm", version=version)
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler(feature_range=(0, 1))
    
    def build_model(self, input_shape: Tuple[int, int]) -> None:
        """Build the hybrid CNN-LSTM model architecture."""
        # CNN branch for spatial features
        cnn_input = Input(shape=input_shape)
        cnn = Conv1D(filters=64, kernel_size=3, activation='relu')(cnn_input)
        cnn = MaxPooling1D(pool_size=2)(cnn)
        cnn = Conv1D(filters=128, kernel_size=3, activation='relu')(cnn)
        cnn = MaxPooling1D(pool_size=2)(cnn)
        cnn = Flatten()(cnn)
        
        # LSTM branch for temporal features
        lstm_input = Input(shape=input_shape)
        lstm = LSTM(50, return_sequences=True)(lstm_input)
        lstm = Dropout(0.2)(lstm)
        lstm = LSTM(50)(lstm)
        lstm = Dropout(0.2)(lstm)
        
        # Combine CNN and LSTM branches
        combined = Concatenate()([cnn, lstm])
        
        # Output layers
        dense = Dense(64, activation='relu')(combined)
        output = Dense(1)(dense)
        
        # Create model
        self.model = Model(inputs=[cnn_input, lstm_input], outputs=output)
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=MODEL['learning_rate']),
            loss='mean_squared_error'
        )
        
        logger.info(f"Built hybrid CNN-LSTM model with input shape {input_shape}")
    
    def preprocess(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess data for hybrid CNN-LSTM model."""
        # Select relevant features
        features = data[['temperature', 'humidity', 'wind_speed', 'pressure']].values
        
        # Scale the features
        scaled_features = self.scaler.fit_transform(features)
        
        # Create sequences
        X, y = [], []
        for i in range(len(scaled_features) - self.sequence_length):
            X.append(scaled_features[i:i + self.sequence_length])
            y.append(scaled_features[i + self.sequence_length, 0])  # Temperature is the target
        
        X = np.array(X)
        y = np.array(y)
        
        return X, y
    
    def train(self, data: pd.DataFrame, target: Optional[pd.Series] = None) -> Dict[str, Any]:
        """Train the hybrid CNN-LSTM model."""
        # Preprocess data
        X, y = self.preprocess(data)
        
        # Split into train and validation sets
        split_idx = int(len(X) * (1 - MODEL['validation_split']))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Build model if not already built
        if self.model is None:
            self.build_model(input_shape=(X_train.shape[1], X_train.shape[2]))
        
        # Set up callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ModelCheckpoint(self.model_path, save_best_only=True)
        ]
        
        # Train model
        history = self.model.fit(
            [X_train, X_train],  # Same input for both branches
            y_train,
            epochs=MODEL['epochs'],
            batch_size=MODEL['batch_size'],
            validation_data=([X_val, X_val], y_val),
            callbacks=callbacks,
            verbose=1
        )
        
        # Save model and scaler
        self.save()
        
        return {
            "history": history.history,
            "final_train_loss": history.history['loss'][-1],
            "final_val_loss": history.history['val_loss'][-1]
        }
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Make predictions using the hybrid CNN-LSTM model."""
        # Ensure model is loaded
        if self.model is None:
            self.load()
            if self.model is None:
                raise ValueError("Model not found. Please train the model first.")
        
        # Preprocess data
        X, _ = self.preprocess(data)
        
        # Make predictions
        scaled_predictions = self.model.predict([X, X])
        
        # Inverse transform to get actual values
        # Create a dummy array with the right shape for inverse_transform
        dummy = np.zeros((len(scaled_predictions), 4))
        dummy[:, 0] = scaled_predictions.flatten()
        
        # Inverse transform
        predictions = self.scaler.inverse_transform(dummy)[:, 0]
        
        return predictions
    
    def evaluate(self, data: pd.DataFrame, target: pd.Series) -> Dict[str, float]:
        """Evaluate the hybrid CNN-LSTM model."""
        # Make predictions
        predictions = self.predict(data)
        
        # Calculate metrics
        mse = mean_squared_error(target, predictions)
        mae = mean_absolute_error(target, predictions)
        rmse = np.sqrt(mse)
        
        return {
            "mse": mse,
            "mae": mae,
            "rmse": rmse
        }


class AnomalyDetector(BaseModel):
    """Model for detecting weather anomalies."""
    
    def __init__(self, version: str = MODEL['version']):
        super().__init__(name="anomaly_detector", version=version)
        self.scaler = MinMaxScaler(feature_range=(0, 1))
    
    def build_model(self, input_shape: int) -> None:
        """Build the anomaly detection model (autoencoder)."""
        # Encoder
        input_layer = Input(shape=(input_shape,))
        encoded = Dense(64, activation='relu')(input_layer)
        encoded = Dense(32, activation='relu')(encoded)
        encoded = Dense(16, activation='relu')(encoded)
        
        # Decoder
        decoded = Dense(32, activation='relu')(encoded)
        decoded = Dense(64, activation='relu')(decoded)
        decoded = Dense(input_shape, activation='sigmoid')(decoded)
        
        # Autoencoder model
        self.model = Model(inputs=input_layer, outputs=decoded)
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=MODEL['learning_rate']),
            loss='mean_squared_error'
        )
        
        logger.info(f"Built anomaly detection model with input shape {input_shape}")
    
    def preprocess(self, data: pd.DataFrame) -> np.ndarray:
        """Preprocess data for anomaly detection."""
        # Select relevant features
        features = data[['temperature', 'humidity', 'pressure', 'wind_speed', 'ion_level', 'vorticity']].values
        
        # Scale the features
        scaled_features = self.scaler.fit_transform(features)
        
        return scaled_features
    
    def train(self, data: pd.DataFrame, target: Optional[pd.Series] = None) -> Dict[str, Any]:
        """Train the anomaly detection model."""
        # Preprocess data
        X = self.preprocess(data)
        
        # Split into train and validation sets
        split_idx = int(len(X) * (1 - MODEL['validation_split']))
        X_train, X_val = X[:split_idx], X[split_idx:]
        
        # Build model if not already built
        if self.model is None:
            self.build_model(input_shape=X_train.shape[1])
        
        # Set up callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ModelCheckpoint(self.model_path, save_best_only=True)
        ]
        
        # Train model
        history = self.model.fit(
            X_train, X_train,  # Autoencoder reconstructs the input
            epochs=MODEL['epochs'],
            batch_size=MODEL['batch_size'],
            validation_data=(X_val, X_val),
            callbacks=callbacks,
            verbose=1
        )
        
        # Save model and scaler
        self.save()
        
        return {
            "history": history.history,
            "final_train_loss": history.history['loss'][-1],
            "final_val_loss": history.history['val_loss'][-1]
        }
    
    def predict(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Detect anomalies in the data."""
        # Ensure model is loaded
        if self.model is None:
            self.load()
            if self.model is None:
                raise ValueError("Model not found. Please train the model first.")
        
        # Preprocess data
        X = self.preprocess(data)
        
        # Reconstruct the input
        X_pred = self.model.predict(X)
        
        # Calculate reconstruction error
        mse = np.mean(np.power(X - X_pred, 2), axis=1)
        
        # Determine anomalies (e.g., using threshold)
        threshold = np.percentile(mse, 95)  # 95th percentile as threshold
        anomalies = mse > threshold
        
        return mse, anomalies
    
    def evaluate(self, data: pd.DataFrame, target: pd.Series) -> Dict[str, float]:
        """Evaluate the anomaly detection model."""
        # This is a simplified evaluation for demonstration
        # In a real scenario, you would need labeled anomalies for proper evaluation
        
        # Detect anomalies
        mse, predicted_anomalies = self.predict(data)
        
        # If target contains actual anomaly labels (1 for anomaly, 0 for normal)
        if target is not None:
            # Calculate metrics
            from sklearn.metrics import precision_score, recall_score, f1_score
            
            precision = precision_score(target, predicted_anomalies)
            recall = recall_score(target, predicted_anomalies)
            f1 = f1_score(target, predicted_anomalies)
            
            return {
                "precision": precision,
                "recall": recall,
                "f1": f1
            }
        
        # If no labeled data, just return the threshold and anomaly count
        return {
            "threshold": np.percentile(mse, 95),
            "anomaly_count": np.sum(predicted_anomalies),
            "anomaly_percentage": np.mean(predicted_anomalies) * 100
        }
