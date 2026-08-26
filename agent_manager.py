from typing import Any, Dict, List, Optional
from base_agent import BaseAgent


class AgentManager:
    """
    Manages multiple agents in the multi-agent system.
    """
    
    def __init__(self):
        """Initialize the agent manager."""
        self.agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent) -> bool:
        """
        Register a new agent with the manager.
        """
        if agent.name in self.agents:
            raise ValueError(f"Agent with name '{agent.name}' is already registered.")
        
        self.agents[agent.name] = agent
        print(f"✓ Agent registered: {agent.name}")
        return True
    
    def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent from the manager.
        """
        if agent_name not in self.agents:
            return False
        
        del self.agents[agent_name]
        print(f"✓ Agent unregistered: {agent_name}")
        return True
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name.
        """
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all registered agents with their information.
        """
        return [agent.get_info() for agent in self.agents.values()]
    
    def execute_agent(
        self,
        agent_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific agent.
        """
        agent = self.get_agent(agent_name)
        
        if not agent:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found.",
                "data": None
            }
        
        try:
            result = agent.execute(input_data)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing agent '{agent_name}': {str(e)}",
                "data": None
            }
    
    def execute_pipeline(
        self,
        pipeline: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a pipeline of agents sequentially.
        """
        results = []
        context = {}
        
        for i, step in enumerate(pipeline):
            agent_name = step.get("agent")
            input_data = step.get("input", {})
            
            # Allow using previous agent's output as context
            if step.get("use_context", False) and context:
                input_data.update(context)
            
            result = self.execute_agent(agent_name, input_data)
            results.append({
                "step": i + 1,
                "agent": agent_name,
                "result": result
            })
            
            # Store data for next agent if needed
            if result.get("success") and result.get("data"):
                context = result.get("data")
        
        return {
            "success": all(r["result"].get("success", False) for r in results),
            "total_steps": len(pipeline),
            "results": results
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get information about the multi-agent system."""
        return {
            "total_agents": len(self.agents),
            "agents": self.list_agents()
        }
