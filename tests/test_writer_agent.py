from unittest.mock import MagicMock, patch
import pytest
from writer_agent import WriterAgent


def test_writer_invalid_input():
    agent = WriterAgent(api_key="fake_groq_key")
    # Missing research_data
    res1 = agent.execute({"topic": "AI in healthcare"})
    assert res1["success"] is False

    # Missing topic
    res2 = agent.execute({"research_data": []})
    assert res2["success"] is False


def test_writer_execution_mocked():
    agent = WriterAgent(api_key="fake_groq_key")
    mock_response = MagicMock()
    mock_response.content = "# Research Report: Autonomous AI Agents\n\n## Executive Summary\nTest summary."

    with patch.object(agent, "_invoke_chain", return_value=mock_response):
        result = agent.execute({
            "topic": "Autonomous AI Agents",
            "research_data": [
                {"url": "https://example.com/ai", "content": "Sample content about autonomous agents."}
            ]
        })

    assert result["success"] is True
    assert "Executive Summary" in result["data"]["report"]
    assert "estimated_tokens" in result["data"]
    assert "estimated_cost_usd" in result["data"]
    assert result["data"]["estimated_tokens"] >= 1


def test_writer_context_guard():
    agent = WriterAgent(api_key="fake_groq_key")
    mock_response = MagicMock()
    mock_response.content = "# Truncated Context Report"

    huge_content = "X" * 150_000
    with patch.object(agent, "_invoke_chain", return_value=mock_response) as mock_invoke:
        result = agent.execute({
            "topic": "Huge input test",
            "research_data": [{"url": "https://example.com/huge", "content": huge_content}]
        })

    assert result["success"] is True
    # Verify the chain was called and token safety was enforced
    call_args = mock_invoke.call_args[0]
    passed_context = call_args[1]["context"]
    assert len(passed_context) < 150_000
    assert "[Context truncated for token safety]" in passed_context
