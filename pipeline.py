import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from agent_manager import AgentManager
from search_agent import SearchAgent
from reader_agent import ReaderAgent
from writer_agent import WriterAgent
from critique_agent import CritiqueAgent
from config import Config
from utils import save_result_to_file, setup_logging


class Pipeline:
    """
    Orchestrates the workflow of multiple agents in sequence.
    Flow: Search → Read → Write → Critique
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the pipeline with all agents.
        """
        self.config = config or Config()
        self.logger = setup_logging(self.config.log_level)
        self.manager = AgentManager()
        self.execution_history: List[Dict[str, Any]] = []
        
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize and register all agents with the manager."""
        try:
            search_agent = SearchAgent(
                api_key=self.config.serp_api_key,
                config=self.config.search_agent_config
            )
            self.manager.register_agent(search_agent)
            
            reader_agent = ReaderAgent(
                config={
                    "timeout": 15,
                    "max_chars_per_page": 5000
                }
            )
            self.manager.register_agent(reader_agent)
            
            writer_agent = WriterAgent(
                config={
                    "model_name": "llama-3.3-70b-versatile",
                    "temperature": 0.5
                }
            )
            self.manager.register_agent(writer_agent)
            
            critique_agent = CritiqueAgent(
                api_key=self.config.groq_api_key,
                config={
                    "model_name": "llama-3.3-70b-versatile",
                    "temperature": 0.3
                }
            )
            self.manager.register_agent(critique_agent)
            
            self.logger.info("✓ All agents initialized successfully")
        except Exception as e:
            self.logger.error(f"✗ Error initializing agents: {str(e)}")
            raise
    
    def execute(
        self,
        topic: str,
        num_search_results: int = 5,
        max_pages_to_read: int = 3,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the complete pipeline workflow.
        """
        pipeline_start = datetime.now()
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Starting Pipeline for Topic: {topic}")
        self.logger.info(f"{'='*60}\n")
        
        result = {
            "success": False,
            "topic": topic,
            "timestamp": pipeline_start.isoformat(),
            "stages": {
                "search": None,
                "read": None,
                "write": None,
                "critique": None
            },
            "final_report": None,
            "critique_feedback": None,
            "error": None
        }
        
        try:
            # Search
            self.logger.info(f"[Stage 1] Searching for: {topic}")
            search_result = self._execute_search_stage(topic, num_search_results)
            result["stages"]["search"] = search_result
            
            if not search_result["success"]:
                result["error"] = "Search stage failed"
                return result
            
            # Extract URLs from search results
            urls = [res.get("link") for res in search_result["data"]["results"] if res.get("link")]
            
            if not urls:
                result["error"] = "No URLs found in search results"
                return result
            
            # Read
            self.logger.info(f"[Stage 2] Reading {len(urls)} URLs")
            read_result = self._execute_read_stage(urls, max_pages_to_read)
            result["stages"]["read"] = read_result
            
            if not read_result["success"]:
                result["error"] = "Read stage failed"
                return result
            
            # Write
            self.logger.info(f"[Stage 3] Generating comprehensive report")
            write_result = self._execute_write_stage(
                topic,
                read_result["data"]["scraped_contents"]
            )
            result["stages"]["write"] = write_result
            
            if not write_result["success"]:
                result["error"] = "Write stage failed"
                return result
            
            # Critique
            self.logger.info(f"[Stage 4] Critiquing and evaluating report")
            critique_result = self._execute_critique_stage(
                topic,
                write_result["data"]["report"]
            )
            result["stages"]["critique"] = critique_result
            
            if critique_result["success"]:
                result["critique_feedback"] = critique_result["data"]["feedback"]
            
            result["success"] = True
            result["final_report"] = write_result["data"]["report"]
            
            if save_results:
                filename = f"pipeline_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                save_result_to_file(result, filename)
                self.logger.info(f"\n✓ Results saved to {filename}")
            
            pipeline_end = datetime.now()
            duration = (pipeline_end - pipeline_start).total_seconds()
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"✓ Pipeline completed successfully in {duration:.2f}s")
            self.logger.info(f"{'='*60}\n")
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            self.logger.error(f"✗ Pipeline execution failed: {str(e)}")
            result["error"] = str(e)
            return result
    
    def _execute_search_stage(self, topic: str, num_results: int) -> Dict[str, Any]:
        """Execute the search stage."""
        try:
            search_agent = self.manager.get_agent("SearchAgent")
            result = search_agent.execute({
                "query": topic,
                "num_results": num_results,
                "include_metadata": True
            })
            
            if result["success"]:
                self.logger.info(f"✓ Found {len(result['data']['results'])} search results")
            
            return result
        except Exception as e:
            self.logger.error(f"Search stage error: {str(e)}")
            return {"success": False, "error": str(e), "data": None}
    
    def _execute_read_stage(self, urls: List[str], max_pages: int) -> Dict[str, Any]:
        """Execute the read stage."""
        try:
            reader_agent = self.manager.get_agent("ReaderAgent")
            result = reader_agent.execute({
                "urls": urls,
                "max_pages": max_pages
            })
            
            if result["success"]:
                num_scraped = len(result["data"]["scraped_contents"])
                self.logger.info(f"✓ Successfully scraped {num_scraped} pages")
            
            return result
        except Exception as e:
            self.logger.error(f"Read stage error: {str(e)}")
            return {"success": False, "error": str(e), "data": None}
    
    def _execute_write_stage(
        self,
        topic: str,
        research_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute the write stage."""
        try:
            writer_agent = self.manager.get_agent("WriterAgent")
            result = writer_agent.execute({
                "topic": topic,
                "research_data": research_data
            })
            
            if result["success"]:
                self.logger.info(f"✓ Report generated successfully")
            
            return result
        except Exception as e:
            self.logger.error(f"Write stage error: {str(e)}")
            return {"success": False, "error": str(e), "data": None}
    
    def _execute_critique_stage(
        self,
        topic: str,
        report: str
    ) -> Dict[str, Any]:
        """Execute the critique stage."""
        try:
            critique_agent = self.manager.get_agent("CritiqueAgent")
            result = critique_agent.execute({
                "topic": topic,
                "report": report
            })
            
            if result["success"]:
                self.logger.info(f"✓ Report critique completed successfully")
            
            return result
        except Exception as e:
            self.logger.error(f"Critique stage error: {str(e)}")
            return {"success": False, "error": str(e), "data": None}
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get all pipeline execution history."""
        return self.execution_history
    
    def get_agent_info(self) -> List[Dict[str, Any]]:
        """Get information about all registered agents."""
        return self.manager.list_agents()


if __name__ == "__main__":
    try:
        pipeline = Pipeline()
        
        # Show agents
        print("\nRegistered Agents:")
        for agent_info in pipeline.get_agent_info():
            print(f"  - {agent_info['name']}: {agent_info['description']}")
        print()
        
        # Execute pipeline
        result = pipeline.execute(
            topic="artificial intelligence applications",
            num_search_results=3,
            max_pages_to_read=2
        )
        
        print("\n" + "="*60)
        print("PIPELINE EXECUTION RESULT")
        print("="*60)
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"Error: {str(e)}")
