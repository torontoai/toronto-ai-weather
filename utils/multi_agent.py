"""
Multi-agent architecture for Toronto AI Weather.

This module implements the Agent-to-Agent (A2A) communication and 
Multi-agent Cognitive Protocol (MCP) for distributed intelligence.
"""

import logging
import asyncio
import json
import uuid
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Enum for agent roles in the system."""
    DATA_COLLECTOR = "data_collector"
    DATA_PROCESSOR = "data_processor"
    MODEL_TRAINER = "model_trainer"
    PREDICTION_ENGINE = "prediction_engine"
    ANOMALY_DETECTOR = "anomaly_detector"
    FEEDBACK_ANALYZER = "feedback_analyzer"
    SYSTEM_MONITOR = "system_monitor"
    COORDINATOR = "coordinator"

class MessageType(Enum):
    """Enum for message types in A2A communication."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"
    MODEL_UPDATE = "model_update"
    PERFORMANCE_METRIC = "performance_metric"
    ANOMALY_ALERT = "anomaly_alert"
    SYSTEM_STATUS = "system_status"

class Message:
    """Class representing a message in A2A communication."""
    
    def __init__(
        self,
        sender_id: str,
        sender_role: AgentRole,
        message_type: MessageType,
        content: Dict[str, Any],
        recipient_id: Optional[str] = None,
        recipient_role: Optional[AgentRole] = None,
        message_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.message_id = message_id or str(uuid.uuid4())
        self.sender_id = sender_id
        self.sender_role = sender_role
        self.recipient_id = recipient_id
        self.recipient_role = recipient_role
        self.message_type = message_type
        self.content = content
        self.in_reply_to = in_reply_to
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "sender_role": self.sender_role.value,
            "recipient_id": self.recipient_id,
            "recipient_role": self.recipient_role.value if self.recipient_role else None,
            "message_type": self.message_type.value,
            "content": self.content,
            "in_reply_to": self.in_reply_to,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        return cls(
            message_id=data.get("message_id"),
            sender_id=data["sender_id"],
            sender_role=AgentRole(data["sender_role"]),
            recipient_id=data.get("recipient_id"),
            recipient_role=AgentRole(data["recipient_role"]) if data.get("recipient_role") else None,
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            in_reply_to=data.get("in_reply_to"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        )

class Agent:
    """Base class for agents in the system."""
    
    def __init__(self, agent_id: str, role: AgentRole):
        self.agent_id = agent_id
        self.role = role
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
    
    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Register a handler for a specific message type."""
        self.message_handlers[message_type] = handler
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle an incoming message."""
        if message.message_type in self.message_handlers:
            return await self.message_handlers[message.message_type](message)
        
        logger.warning(f"No handler for message type {message.message_type} in agent {self.agent_id}")
        return None
    
    async def send_message(self, message: Message) -> None:
        """Send a message to the message bus."""
        await MessageBus.get_instance().publish(message)
    
    async def receive_message(self, message: Message) -> None:
        """Receive a message from the message bus."""
        await self.message_queue.put(message)
    
    async def run(self) -> None:
        """Run the agent's main loop."""
        self.running = True
        while self.running:
            message = await self.message_queue.get()
            response = await self.handle_message(message)
            if response:
                await self.send_message(response)
            self.message_queue.task_done()
    
    def stop(self) -> None:
        """Stop the agent's main loop."""
        self.running = False

class MessageBus:
    """Singleton class for message bus in A2A communication."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'MessageBus':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if MessageBus._instance is not None:
            raise RuntimeError("Use MessageBus.get_instance() to get the singleton instance")
        
        self.subscribers: Dict[str, Agent] = {}
        self.role_subscribers: Dict[AgentRole, List[Agent]] = {role: [] for role in AgentRole}
    
    def subscribe(self, agent: Agent) -> None:
        """Subscribe an agent to the message bus."""
        self.subscribers[agent.agent_id] = agent
        self.role_subscribers[agent.role].append(agent)
        logger.info(f"Agent {agent.agent_id} with role {agent.role} subscribed to message bus")
    
    def unsubscribe(self, agent_id: str) -> None:
        """Unsubscribe an agent from the message bus."""
        if agent_id in self.subscribers:
            agent = self.subscribers[agent_id]
            self.role_subscribers[agent.role].remove(agent)
            del self.subscribers[agent_id]
            logger.info(f"Agent {agent_id} unsubscribed from message bus")
    
    async def publish(self, message: Message) -> None:
        """Publish a message to the message bus."""
        if message.recipient_id:
            # Direct message to specific agent
            if message.recipient_id in self.subscribers:
                await self.subscribers[message.recipient_id].receive_message(message)
            else:
                logger.warning(f"Recipient agent {message.recipient_id} not found")
        elif message.recipient_role:
            # Broadcast to all agents with specific role
            for agent in self.role_subscribers[message.recipient_role]:
                await agent.receive_message(message)
        else:
            # Broadcast to all agents
            for agent in self.subscribers.values():
                await agent.receive_message(message)

class DataCollectorAgent(Agent):
    """Agent responsible for collecting data from various sources."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentRole.DATA_COLLECTOR)
        self.register_handler(MessageType.TASK_ASSIGNMENT, self.handle_task_assignment)
        self.register_handler(MessageType.REQUEST, self.handle_request)
        self.data_sources = {}
    
    async def handle_task_assignment(self, message: Message) -> Message:
        """Handle task assignment messages."""
        task = message.content.get("task")
        if task == "collect_data":
            source = message.content.get("source")
            # Simulate data collection
            logger.info(f"Collecting data from {source}")
            
            # Return task completion message
            return Message(
                sender_id=self.agent_id,
                sender_role=self.role,
                recipient_id=message.sender_id,
                recipient_role=message.sender_role,
                message_type=MessageType.TASK_COMPLETION,
                content={
                    "task": task,
                    "source": source,
                    "status": "completed",
                    "data_summary": {
                        "records": 100,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                },
                in_reply_to=message.message_id
            )
        
        return Message(
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=message.sender_id,
            recipient_role=message.sender_role,
            message_type=MessageType.RESPONSE,
            content={"error": "Unknown task"},
            in_reply_to=message.message_id
        )
    
    async def handle_request(self, message: Message) -> Message:
        """Handle request messages."""
        request_type = message.content.get("request_type")
        if request_type == "data_source_status":
            # Return data source status
            return Message(
                sender_id=self.agent_id,
                sender_role=self.role,
                recipient_id=message.sender_id,
                recipient_role=message.sender_role,
                message_type=MessageType.RESPONSE,
                content={
                    "data_sources": {
                        "noaa": "active",
                        "eccc": "active",
                        "satellite": "active",
                        "social_media": "active"
                    }
                },
                in_reply_to=message.message_id
            )
        
        return Message(
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=message.sender_id,
            recipient_role=message.sender_role,
            message_type=MessageType.RESPONSE,
            content={"error": "Unknown request type"},
            in_reply_to=message.message_id
        )

class ModelTrainerAgent(Agent):
    """Agent responsible for training machine learning models."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentRole.MODEL_TRAINER)
        self.register_handler(MessageType.TASK_ASSIGNMENT, self.handle_task_assignment)
        self.register_handler(MessageType.REQUEST, self.handle_request)
        self.models = {}
    
    async def handle_task_assignment(self, message: Message) -> Message:
        """Handle task assignment messages."""
        task = message.content.get("task")
        if task == "train_model":
            model_type = message.content.get("model_type")
            # Simulate model training
            logger.info(f"Training model {model_type}")
            
            # Return task completion message
            return Message(
                sender_id=self.agent_id,
                sender_role=self.role,
                recipient_id=message.sender_id,
                recipient_role=message.sender_role,
                message_type=MessageType.TASK_COMPLETION,
                content={
                    "task": task,
                    "model_type": model_type,
                    "status": "completed",
                    "performance": {
                        "accuracy": 0.92,
                        "loss": 0.08
                    }
                },
                in_reply_to=message.message_id
            )
        
        return Message(
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=message.sender_id,
            recipient_role=message.sender_role,
            message_type=MessageType.RESPONSE,
            content={"error": "Unknown task"},
            in_reply_to=message.message_id
        )
    
    async def handle_request(self, message: Message) -> Message:
        """Handle request messages."""
        request_type = message.content.get("request_type")
        if request_type == "model_status":
            # Return model status
            return Message(
                sender_id=self.agent_id,
                sender_role=self.role,
                recipient_id=message.sender_id,
                recipient_role=message.sender_role,
                message_type=MessageType.RESPONSE,
                content={
                    "models": {
                        "temperature_lstm": {
                            "status": "trained",
                            "version": "1.0.0",
                            "accuracy": 0.92
                        },
                        "hybrid_cnn_lstm": {
                            "status": "training",
                            "progress": 0.75
                        }
                    }
                },
                in_reply_to=message.message_id
            )
        
        return Message(
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=message.sender_id,
            recipient_role=message.sender_role,
            message_type=MessageType.RESPONSE,
            content={"error": "Unknown request type"},
            in_reply_to=message.message_id
        )

class CoordinatorAgent(Agent):
    """Agent responsible for coordinating other agents."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentRole.COORDINATOR)
        self.register_handler(MessageType.TASK_COMPLETION, self.handle_task_completion)
        self.register_handler(MessageType.PERFORMANCE_METRIC, self.handle_performance_metric)
        self.register_handler(MessageType.ANOMALY_ALERT, self.handle_anomaly_alert)
        self.register_handler(MessageType.SYSTEM_STATUS, self.handle_system_status)
        self.tasks = {}
        self.performance_metrics = {}
        self.anomalies = []
        self.system_status = {}
    
    async def handle_task_completion(self, message: Message) -> None:
        """Handle task completion messages."""
        task = message.content.get("task")
        status = message.content.get("status")
        
        logger.info(f"Task {task} completed with status {status}")
        
        # Update task status
        self.tasks[message.in_reply_to] = {
            "task": task,
            "status": status,
            "completed_by": message.sender_id,
            "completed_at": datetime.utcnow()
        }
        
        # No response needed
        return None
    
    async def handle_performance_metric(self, message: Message) -> None:
        """Handle performance metric messages."""
        metric_type = message.content.get("metric_type")
        value = message.content.get("value")
        
        logger.info(f"Performance metric {metric_type}: {value}")
        
        # Update performance metrics
        if metric_type not in self.performance_metrics:
            self.performance_metrics[metric_type] = []
        
        self.performance_metrics[metric_type].append({
            "value": value,
            "timestamp": datetime.utcnow(),
            "reported_by": message.sender_id
        })
        
        # No response needed
        return None
    
    async def handle_anomaly_alert(self, message: Message) -> Message:
        """Handle anomaly alert messages."""
        anomaly_type = message.content.get("anomaly_type")
        severity = message.content.get("severity")
        
        logger.warning(f"Anomaly alert: {anomaly_type} (severity: {severity})")
        
        # Record anomaly
        self.anomalies.append({
            "type": anomaly_type,
            "severity": severity,
            "reported_by": message.sender_id,
            "timestamp": datetime.utcnow(),
            "details": message.content.get("details", {})
        })
        
        # Acknowledge receipt
        return Message(
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=message.sender_id,
            recipient_role=message.sender_role,
            message_type=MessageType.RESPONSE,
            content={"status": "acknowledged"},
            in_reply_to=message.message_id
        )
    
    async def handle_system_status(self, message: Message) -> None:
        """Handle system status messages."""
        component = message.content.get("component")
        status = message.content.get("status")
        
        logger.info(f"System status update: {component} is {status}")
        
        # Update system status
        self.system_status[component] = {
            "status": status,
            "updated_at": datetime.utcnow(),
            "reported_by": message.sender_id
        }
        
        # No response needed
        return None
    
    async def assign_task(self, recipient_role: AgentRole, task: Dict[str, Any]) -> None:
        """Assign a task to agents with a specific role."""
        message = Message(
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_role=recipient_role,
            message_type=MessageType.TASK_ASSIGNMENT,
            content=task
        )
        
        await self.send_message(message)
        
        # Record task assignment
        self.tasks[message.message_id] = {
            "task": task.get("task"),
            "assigned_to_role": recipient_role.value,
            "assigned_at": datetime.utcnow(),
            "status": "assigned"
        }

class MultiAgentSystem:
    """Class for managing the multi-agent system."""
    
    def __init__(self):
        self.message_bus = MessageBus.get_instance()
        self.agents = {}
        self.tasks = []
    
    def create_agent(self, role: AgentRole) -> Agent:
        """Create an agent with a specific role."""
        agent_id = f"{role.value}_{len(self.agents) + 1}"
        
        if role == AgentRole.DATA_COLLECTOR:
            agent = DataCollectorAgent(agent_id)
        elif role == AgentRole.MODEL_TRAINER:
            agent = ModelTrainerAgent(agent_id)
        elif role == AgentRole.COORDINATOR:
            agent = CoordinatorAgent(agent_id)
        else:
            # Default agent for other roles
            agent = Agent(agent_id, role)
        
        self.agents[agent_id] = agent
        self.message_bus.subscribe(agent)
        
        return agent
    
    async def start_agents(self) -> None:
        """Start all agents."""
        tasks = []
        for agent in self.agents.values():
            task = asyncio.create_task(agent.run())
            tasks.append(task)
        
        self.tasks = tasks
    
    async def stop_agents(self) -> None:
        """Stop all agents."""
        for agent in self.agents.values():
            agent.stop()
        
        for task in self.tasks:
            task.cancel()
        
        self.tasks = []

# Example usage
async def run_example():
    """Run an example of the multi-agent system."""
    system = MultiAgentSystem()
    
    # Create agents
    coordinator = system.create_agent(AgentRole.COORDINATOR)
    data_collector = system.create_agent(AgentRole.DATA_COLLECTOR)
    model_trainer = system.create_agent(AgentRole.MODEL_TRAINER)
    
    # Start agents
    await system.start_agents()
    
    # Assign tasks
    await coordinator.assign_task(AgentRole.DATA_COLLECTOR, {
        "task": "collect_data",
        "source": "noaa"
    })
    
    await coordinator.assign_task(AgentRole.MODEL_TRAINER, {
        "task": "train_model",
        "model_type": "temperature_lstm"
    })
    
    # Wait for tasks to complete
    await asyncio.sleep(5)
    
    # Stop agents
    await system.stop_agents()

if __name__ == "__main__":
    asyncio.run(run_example())
