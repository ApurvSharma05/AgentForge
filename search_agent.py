"""
Search Agent for the multi-agent system.
Uses Serp API to search the internet and collect information.
"""

import requests
from typing import Any, Dict, List, Optional
from base_agent import BaseAgent


class SearchAgent(BaseAgent):
    """
    Search agent that queries Serp API for internet search results.
    
    Attributes:
        api_key: Serp API key for authentication
        base_url: Serp API base URL
    """
    
    SERP_API_URL = "https://serpapi.com/search"
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the search agent.
        
        Args:
            api_key: Serp API key
            config: Optional configuration with defaults for search parameters
        """
        super().__init__(
            name="SearchAgent",
            description="Searches the internet using Serp API to collect information",
            config=config or {}
        )
        self.api_key = api_key
        self.timeout = self.config.get("timeout", 15)
        self.max_results = self.config.get("max_results", 10)
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate search input data.
        
        Args:
            input_data: Must contain 'query' key
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(input_data, dict):
            return False
        
        if "query" not in input_data:
            return False
        
        if not isinstance(input_data["query"], str) or not input_data["query"].strip():
            return False
        
        return True
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a search query.
        
        Args:
            input_data: Dictionary containing:
                - query (str): Search query
                - num_results (int, optional): Number of results to return (default: 10)
                - include_metadata (bool, optional): Include metadata (default: True)
        
        Returns:
            Dictionary containing search results and metadata
        """
        if not self.validate_input(input_data):
            return {
                "success": False,
                "error": "Invalid input. 'query' key is required and must be a non-empty string.",
                "data": None
            }
        
        try:
            query = input_data.get("query", "").strip()
            num_results = input_data.get("num_results", self.max_results)
            include_metadata = input_data.get("include_metadata", True)
            
            results = self._search(query, num_results)
            self.update_execution_time()
            
            return {
                "success": True,
                "error": None,
                "data": {
                    "query": query,
                    "results": results,
                    "num_results": len(results),
                    "metadata": self._generate_metadata(query) if include_metadata else None
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Search execution failed: {str(e)}",
                "data": None
            }
    
    def _search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """
        Perform the actual search using SerpAPI.
        
        Args:
            query: Search query string
            num_results: Number of results to return
            
        Returns:
            List of search results
        """
        params = {
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
            "engine": "google"
        }
        
        response = requests.get(
            self.SERP_API_URL,
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        # Extract organic results
        for result in data.get("organic_results", [])[:num_results]:
            results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", ""),
                "position": result.get("position", 0)
            })
        
        return results
    
    def _generate_metadata(self, query: str) -> Dict[str, Any]:
        """
        Generate metadata about the search.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with metadata
        """
        return {
            "query": query,
            "agent_name": self.name,
            "timestamp": self.last_executed.isoformat() if self.last_executed else None,
            "api_used": "Serp API"
        }
    
    def batch_search(self, queries: List[str]) -> Dict[str, Any]:
        """
        Execute multiple searches in batch.
        
        Args:
            queries: List of search queries
            
        Returns:
            Dictionary with batch results
        """
        results = []
        errors = []
        
        for query in queries:
            try:
                result = self.execute({"query": query})
                results.append(result)
            except Exception as e:
                errors.append({
                    "query": query,
                    "error": str(e)
                })
        
        return {
            "success": len(errors) == 0,
            "total_queries": len(queries),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors if errors else None
        }
