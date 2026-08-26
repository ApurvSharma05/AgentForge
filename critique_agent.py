import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from base_agent import BaseAgent

class CritiqueAgent(BaseAgent):
    def __init__(self, api_key: Optional[str]=None, config: Optional[Dict[str, Any]]=None):
        super().__init__(
            name="CritiqueAgent",
            description="Evaluates and provides feedback on research reports using Groq",
            config=config or {}
        )
        
        self.api_key=api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment variables.")

        model_name=self.config.get("model_name", "llama-3.3-70b-versatile")
        temperature=self.config.get("temperature", 0.3)  
        
        self.llm=ChatGroq(
            groq_api_key=self.api_key,
            model_name=model_name,
            temperature=temperature
        )

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "topic" in input_data and "report" in input_data

    def execute(self, input_data: Dict[str, Any])-> Dict[str, Any]:
        if not self.validate_input(input_data):
            return {"success": False, "error": "Missing topic or report content"}

        topic=input_data.get("topic")
        report_content=input_data.get("report")
        
        prompt=ChatPromptTemplate.from_template("""
        You are a Senior Research Editor and Domain Expert. Provide a detailed evaluation of this report on: {topic}
        
        REPORT CONTENT:
        {report}
        
        EVALUATE ON:
        1. **Accuracy & Evidence**: Fact accuracy, claim substantiation, logical consistency
        2. **Depth & Completeness**: Coverage breadth, missing critical aspects, unexplored angles
        3. **Structure & Clarity**: Organization, readability, flow, professional presentation
        4. **Data Quality**: Source credibility, data freshness, evidence strength
        5. **Actionability**: Practical insights, recommendations clarity, business value
        
        PROVIDE:
        - **Overall Score**: Rate 1-10 with reasoning
        - **Strengths**: 3-4 specific strengths with examples
        - **Critical Gaps**: Specific areas needing expansion or correction
        - **Priority Improvements**: Top 3 actionable enhancements
        - **Recommendation**: Pass/Revise with justification
        
        Be specific, data-driven, and constructive.
        """)

        try:
            chain=prompt|self.llm
            print(f"--- {self.name} is reviewing the report for: {topic} ---")
            
            response=chain.invoke({"topic": topic, "report": report_content})
            feedback=response.content
            is_approved="Pass" in feedback or ("Score: 8" in feedback or "Score: 9" in feedback or "Score: 10" in feedback)
            
            if hasattr(self, 'update_execution_time'):
                self.update_execution_time()
            
            return{
                "success": True,
                "data":{
                    "feedback": feedback,
                    "is_approved": is_approved
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Groq execution failed: {str(e)}"}
