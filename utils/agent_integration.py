"""
Integration of multi-agent architecture with the main Toronto AI Weather system.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional

from toronto_ai_weather.utils.multi_agent import (
    MultiAgentSystem, AgentRole, MessageType, Message
)
from toronto_ai_weather.models.models import BaseModel, TemperatureLSTM, HybridCNNLSTM, AnomalyDetector
from toronto_ai_weather.data.ingestion import DataIngestionManager

# Set up logging
logger = logging.getLogger(__name__)

class TorontoAIWeatherAgentSystem:
    """
    Integration class for connecting the multi-agent system with the Toronto AI Weather components.
    This class serves as the bridge between the agent communication framework and the actual
    weather prediction functionality.
    """
    
    def __init__(self):
        self.multi_agent_system = MultiAgentSystem()
        self.data_ingestion_manager = DataIngestionManager()
        self.models = {
            'temperature_lstm': TemperatureLSTM(),
            'hybrid_cnn_lstm': HybridCNNLSTM(),
            'anomaly_detector': AnomalyDetector()
        }
        self.coordinator = None
        self.running = False
    
    async def initialize(self):
        """Initialize the agent system and connect it to the weather components."""
        # Create agents for each role
        self.coordinator = self.multi_agent_system.create_agent(AgentRole.COORDINATOR)
        
        # Create data collector agents
        for i in range(3):  # Create multiple data collectors for different sources
            self.multi_agent_system.create_agent(AgentRole.DATA_COLLECTOR)
        
        # Create data processor agents
        for i in range(2):
            self.multi_agent_system.create_agent(AgentRole.DATA_PROCESSOR)
        
        # Create model trainer agents
        for i in range(2):
            self.multi_agent_system.create_agent(AgentRole.MODEL_TRAINER)
        
        # Create prediction engine agents
        self.multi_agent_system.create_agent(AgentRole.PREDICTION_ENGINE)
        
        # Create anomaly detector agents
        self.multi_agent_system.create_agent(AgentRole.ANOMALY_DETECTOR)
        
        # Create feedback analyzer agents
        self.multi_agent_system.create_agent(AgentRole.FEEDBACK_ANALYZER)
        
        # Create system monitor agents
        self.multi_agent_system.create_agent(AgentRole.SYSTEM_MONITOR)
        
        # Start all agents
        await self.multi_agent_system.start_agents()
        logger.info("Multi-agent system initialized and started")
    
    async def start(self):
        """Start the Toronto AI Weather agent system."""
        if self.running:
            logger.warning("System is already running")
            return
        
        self.running = True
        
        # Initialize the agent system
        await self.initialize()
        
        # Start the main processing loop
        asyncio.create_task(self.main_loop())
        logger.info("Toronto AI Weather agent system started")
    
    async def stop(self):
        """Stop the Toronto AI Weather agent system."""
        if not self.running:
            logger.warning("System is not running")
            return
        
        self.running = False
        
        # Stop all agents
        await self.multi_agent_system.stop_agents()
        logger.info("Toronto AI Weather agent system stopped")
    
    async def main_loop(self):
        """Main processing loop for the agent system."""
        while self.running:
            # Assign data collection tasks
            await self.assign_data_collection_tasks()
            
            # Assign model training tasks periodically
            await self.assign_model_training_tasks()
            
            # Assign prediction tasks
            await self.assign_prediction_tasks()
            
            # Wait before next cycle
            await asyncio.sleep(60)  # 1-minute cycle
    
    async def assign_data_collection_tasks(self):
        """Assign data collection tasks to data collector agents."""
        if not self.coordinator:
            logger.error("Coordinator agent not initialized")
            return
        
        # Assign tasks for different data sources
        data_sources = [
            "noaa", "eccc", "satellite", "social_media", 
            "seismic", "cosmic_ray", "ion", "vorticity"
        ]
        
        for source in data_sources:
            await self.coordinator.assign_task(AgentRole.DATA_COLLECTOR, {
                "task": "collect_data",
                "source": source,
                "priority": "high" if source in ["noaa", "eccc"] else "medium"
            })
    
    async def assign_model_training_tasks(self):
        """Assign model training tasks to model trainer agents."""
        if not self.coordinator:
            logger.error("Coordinator agent not initialized")
            return
        
        # Assign tasks for different models
        model_types = [
            "temperature_lstm", "hybrid_cnn_lstm", "anomaly_detector"
        ]
        
        for model_type in model_types:
            await self.coordinator.assign_task(AgentRole.MODEL_TRAINER, {
                "task": "train_model",
                "model_type": model_type,
                "parameters": {
                    "epochs": 100,
                    "batch_size": 64,
                    "learning_rate": 0.001
                }
            })
    
    async def assign_prediction_tasks(self):
        """Assign prediction tasks to prediction engine agents."""
        if not self.coordinator:
            logger.error("Coordinator agent not initialized")
            return
        
        # Assign prediction tasks
        await self.coordinator.assign_task(AgentRole.PREDICTION_ENGINE, {
            "task": "generate_predictions",
            "location": "toronto",
            "prediction_type": "temperature",
            "time_range": "24h"
        })
        
        # Assign anomaly detection tasks
        await self.coordinator.assign_task(AgentRole.ANOMALY_DETECTOR, {
            "task": "detect_anomalies",
            "data_types": ["ion", "vorticity", "seismic"],
            "sensitivity": "medium"
        })

# Function to run the agent system
async def run_agent_system():
    """Run the Toronto AI Weather agent system."""
    system = TorontoAIWeatherAgentSystem()
    await system.start()
    
    try:
        # Keep the system running
        while True:
            await asyncio.sleep(3600)  # Check every hour
    except KeyboardInterrupt:
        # Stop the system on keyboard interrupt
        await system.stop()

if __name__ == "__main__":
    asyncio.run(run_agent_system())
