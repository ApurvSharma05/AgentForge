from unittest.mock import MagicMock, patch
from critique_agent import CritiqueAgent, CritiqueResult


def test_critique_invalid_input():
    agent = CritiqueAgent(api_key="fake_groq_key")
    # Missing report
    res1 = agent.execute({"topic": "AI Ethics"})
    assert res1["success"] is False

    # Missing topic
    res2 = agent.execute({"report": "Sample report text"})
    assert res2["success"] is False


def test_critique_structured_output_approved():
    agent = CritiqueAgent(api_key="fake_groq_key")
    mock_critique = CritiqueResult(
        overall_score=9,
        strengths=["Clear methodology", "Solid statistics", "Good references"],
        critical_gaps=["Could expand on geopolitical impacts"],
        priority_improvements=["Add comparative benchmark table"],
        recommendation="Pass",
        is_approved=True,
        detailed_feedback="Exceptional research depth and synthesis."
    )

    with patch.object(agent, "_invoke_structured", return_value=mock_critique):
        result = agent.execute({
            "topic": "Quantum Computing",
            "report": "Sample report body"
        })

    assert result["success"] is True
    assert result["data"]["is_approved"] is True
    assert result["data"]["overall_score"] == 9
    assert "### Overall Score: 9/10" in result["data"]["feedback"]
    assert "Pass" in result["data"]["feedback"]
    assert result["data"]["structured_critique"]["recommendation"] == "Pass"


def test_critique_fallback_handling():
    agent = CritiqueAgent(api_key="fake_groq_key")
    mock_response = MagicMock()
    mock_response.content = "Score: 6/10. Needs revision. Strengths: None."

    # Force structured output to raise an exception, triggering text fallback
    with patch.object(agent, "_invoke_structured", side_effect=Exception("Structured parsing error")):
        with patch.object(agent, "_invoke_fallback_chain", return_value=mock_response):
            result = agent.execute({
                "topic": "Quantum Computing",
                "report": "Sample report body"
            })

    assert result["success"] is True
    assert result["data"]["is_approved"] is False
