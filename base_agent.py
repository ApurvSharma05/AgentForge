from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system.
    
    Attributes:
        name: The name/identifier of the agent
        description: A brief description of what the agent does
    """
    
    def __init__(self, name: str, description: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            name: Agent name/identifier
            description: Description of agent's purpose
            config: Optional configuration dictionary
        """
        self.name = name
        self.description = description
        self.config = config or {}
        self.created_at = datetime.now()
        self.last_executed = None
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main functionality.
        
        Args:
            input_data: Dictionary containing input parameters for the agent
            
        Returns:
            Dictionary containing the execution result
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate that the input data is in the expected format.
        
        Args:
            input_data: Dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the agent."""
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "last_executed": self.last_executed.isoformat() if self.last_executed else None
        }
    
    def update_execution_time(self):
        """Update the last execution time."""
        self.last_executed = datetime.now()
