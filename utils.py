"""
Utility functions for the multi-agent system.
"""

import json
import logging
from typing import Any, Dict
from datetime import datetime


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Setup logging for the multi-agent system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("MultiAgentSystem")
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def save_result_to_file(result: Dict[str, Any], filepath: str) -> bool:
    """
    Save agent result to a JSON file.
    
    Args:
        result: Result dictionary to save
        filepath: Path to save the file
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        with open(filepath, "w") as f:
            json.dump(result, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Error saving result to file: {str(e)}")
        return False


def load_result_from_file(filepath: str) -> Dict[str, Any]:
    """
    Load agent result from a JSON file.
    
    Args:
        filepath: Path to load the file from
        
    Returns:
        Result dictionary
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading result from file: {str(e)}")
        return {}


def format_results(results: Dict[str, Any], pretty: bool = True) -> str:
    """
    Format results for display.
    
    Args:
        results: Results dictionary
        pretty: Whether to format with indentation
        
    Returns:
        Formatted string
    """
    if pretty:
        return json.dumps(results, indent=2, default=str)
    return json.dumps(results, default=str)


def merge_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple result dictionaries.
    
    Args:
        results: Dictionary of results to merge
        
    Returns:
        Merged results dictionary
    """
    merged = {
        "merged_at": datetime.now().isoformat(),
        "source_results": results
    }
    return merged
