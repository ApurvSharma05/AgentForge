import logging
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential
from base_agent import BaseAgent 

logger = logging.getLogger("MultiAgentSystem")

class WriterAgent(BaseAgent):
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="WriterAgent",
            description="Drafts structured research reports from gathered data using Groq",
            config=config or {}
        )
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment variables.")

        model_name = self.config.get("model_name", "llama-3.3-70b-versatile")
        temperature = self.config.get("temperature", 0.5)
        
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name=model_name,
            temperature=temperature
        )

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "topic" in input_data and "research_data" in input_data

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _invoke_chain(self, chain: Any, input_vars: Dict[str, Any]) -> Any:
        return chain.invoke(input_vars)

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_input(input_data):
            return {"success": False, "error": "Missing topic or research_data"}

        topic = input_data.get("topic")
        research_results = input_data.get("research_data", [])
        
        context_blocks = [
            f"Source: {item.get('url')}\nContent: {item.get('content')}" 
            for item in research_results
        ]
        full_context = "\n\n---\n\n".join(context_blocks)

        # Context safety guard: truncate if context exceeds 100k chars (~25k tokens)
        MAX_SAFE_CHARS = 100_000
        if len(full_context) > MAX_SAFE_CHARS:
            logger.warning(f"[{self.name}] Context size ({len(full_context):,} chars) exceeds safety limit. Truncating to {MAX_SAFE_CHARS:,} chars.")
            full_context = full_context[:MAX_SAFE_CHARS] + "\n\n[Context truncated for token safety]"

        estimated_tokens = len(full_context) // 4
        estimated_cost_usd = (estimated_tokens / 1_000_000) * 0.59
        logger.info(f"[{self.name}] Estimated context tokens: ~{estimated_tokens:,} (~${estimated_cost_usd:.4f} USD)")

        prompt = ChatPromptTemplate.from_template("""
        You are a Senior Research Analyst. Write a comprehensive, in-depth report on: {topic}
        
        RESEARCH DATA:
        {context}
        
        STRUCTURE (BE THOROUGH & DETAILED):
        1. **Executive Summary** - Key takeaways and insights (200+ words)
        2. **Introduction** - Context and significance of the topic
        3. **Market/Industry Overview** - Landscape, trends, and dynamics
        4. **Key Findings** - Analysis of 4-5 major findings with evidence
        5. **Technical Deep Dive** - Mechanisms, methodologies, implementation details
        6. **Comparative Analysis** - How this contrasts with alternatives/competitors
        7. **Implications & Impact** - Business, technical, or social implications
        8. **Challenges & Limitations** - Known issues, risks, constraints
        9. **Future Outlook** - Emerging trends, projected evolution
        10. **Recommendations** - Actionable next steps (3-5 specific recommendations)
        11. **References** - All sources with URLs
        
        REQUIREMENTS:
        - Minimum 2000 words total
        - Use data and statistics wherever available
        - Include specific examples and case studies
        - Maintain professional, analytical tone
        - Provide nuanced, balanced perspective
        """)

        try:
            chain = prompt | self.llm
            logger.info(f"[{self.name}] Drafting report for: {topic}")
            
            response = self._invoke_chain(chain, {"topic": topic, "context": full_context})
            
            if hasattr(self, 'update_execution_time'):
                self.update_execution_time()
            
            return {
                "success": True,
                "data": {
                    "report": response.content,
                    "estimated_tokens": estimated_tokens,
                    "estimated_cost_usd": round(estimated_cost_usd, 5)
                }
            }
        except Exception as e:
            logger.error(f"[{self.name}] Groq execution failed: {str(e)}")
            return {"success": False, "error": f"Groq execution failed: {str(e)}"}
