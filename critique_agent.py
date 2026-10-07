import logging
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential
from base_agent import BaseAgent

logger = logging.getLogger("MultiAgentSystem")


class CritiqueResult(BaseModel):
    """Structured evaluation output for research reports."""
    overall_score: int = Field(..., ge=1, le=10, description="Overall score from 1 to 10")
    strengths: List[str] = Field(default_factory=list, description="3-4 specific strengths with examples")
    critical_gaps: List[str] = Field(default_factory=list, description="Specific areas needing expansion or correction")
    priority_improvements: List[str] = Field(default_factory=list, description="Top 3 actionable enhancements")
    recommendation: str = Field(..., description="Recommendation: 'Pass' or 'Revise'")
    is_approved: bool = Field(..., description="True if overall_score >= 7 and recommendation == 'Pass'")
    detailed_feedback: Optional[str] = Field(default="", description="Detailed qualitative feedback")


class CritiqueAgent(BaseAgent):
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="CritiqueAgent",
            description="Evaluates and provides feedback on research reports using Groq",
            config=config or {}
        )
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment variables.")

        model_name = self.config.get("model_name", "llama-3.3-70b-versatile")
        temperature = self.config.get("temperature", 0.3)  
        
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name=model_name,
            temperature=temperature
        )

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "topic" in input_data and "report" in input_data

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _invoke_structured(self, structured_llm: Any, prompt_text: str) -> CritiqueResult:
        return structured_llm.invoke(prompt_text)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _invoke_fallback_chain(self, chain: Any, input_vars: Dict[str, Any]) -> Any:
        return chain.invoke(input_vars)

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_input(input_data):
            return {"success": False, "error": "Missing topic or report content"}

        topic = input_data.get("topic")
        report_content = input_data.get("report")
        
        prompt = ChatPromptTemplate.from_template("""
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
        - Overall Score: Rate 1-10 with reasoning
        - Strengths: 3-4 specific strengths with examples
        - Critical Gaps: Specific areas needing expansion or correction
        - Priority Improvements: Top 3 actionable enhancements
        - Recommendation: Pass/Revise with justification
        - is_approved: Set to true if overall_score >= 7 and recommendation is Pass, else false
        """)

        logger.info(f"[{self.name}] Reviewing report for: {topic}")

        try:
            prompt_text = prompt.format(topic=topic, report=report_content)
            structured_llm = self.llm.with_structured_output(CritiqueResult)
            critique: CritiqueResult = self._invoke_structured(structured_llm, prompt_text)

            feedback_md = (
                f"### Overall Score: {critique.overall_score}/10\n"
                f"**Recommendation:** {critique.recommendation} "
                f"({'✅ Approved' if critique.is_approved else '⚠️ Revision Needed'})\n\n"
                f"#### Strengths:\n" + "\n".join(f"- {s}" for s in critique.strengths) + "\n\n"
                f"#### Critical Gaps:\n" + "\n".join(f"- {g}" for g in critique.critical_gaps) + "\n\n"
                f"#### Priority Improvements:\n" + "\n".join(f"- {p}" for p in critique.priority_improvements)
            )
            if critique.detailed_feedback:
                feedback_md += f"\n\n#### Detailed Notes:\n{critique.detailed_feedback}"

            if hasattr(self, 'update_execution_time'):
                self.update_execution_time()

            return {
                "success": True,
                "data": {
                    "feedback": feedback_md,
                    "is_approved": critique.is_approved,
                    "overall_score": critique.overall_score,
                    "structured_critique": critique.model_dump()
                }
            }
        except Exception as e:
            logger.warning(f"[{self.name}] Structured output failed ({str(e)}), attempting fallback...")
            try:
                chain = prompt | self.llm
                response = self._invoke_fallback_chain(chain, {"topic": topic, "report": report_content})
                feedback = response.content
                is_approved = "Pass" in feedback or any(f"Score: {s}" in feedback for s in ["7", "8", "9", "10"])
                
                if hasattr(self, 'update_execution_time'):
                    self.update_execution_time()

                return {
                    "success": True,
                    "data": {
                        "feedback": feedback,
                        "is_approved": is_approved,
                        "overall_score": 8 if is_approved else 5,
                        "structured_critique": None
                    }
                }
            except Exception as e2:
                logger.error(f"[{self.name}] Groq execution failed: {str(e2)}")
                return {"success": False, "error": f"Groq execution failed: {str(e2)}"}
