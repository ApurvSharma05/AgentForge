from unittest.mock import MagicMock, patch
import pytest
from pipeline import Pipeline
from config import Config


@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.serp_api_key = "fake_serp_key"
    config.groq_api_key = "fake_groq_key"
    config.log_level = "INFO"
    config.search_agent_config = {"timeout": 15, "max_results": 5}
    return config


def test_pipeline_initialization(mock_config):
    with patch("pipeline.SearchAgent") as mock_search, \
         patch("pipeline.ReaderAgent") as mock_reader, \
         patch("pipeline.WriterAgent") as mock_writer, \
         patch("pipeline.CritiqueAgent") as mock_critique:
        
        mock_search.return_value.name = "SearchAgent"
        mock_search.return_value.get_info.return_value = {"name": "SearchAgent"}
        mock_reader.return_value.name = "ReaderAgent"
        mock_reader.return_value.get_info.return_value = {"name": "ReaderAgent"}
        mock_writer.return_value.name = "WriterAgent"
        mock_writer.return_value.get_info.return_value = {"name": "WriterAgent"}
        mock_critique.return_value.name = "CritiqueAgent"
        mock_critique.return_value.get_info.return_value = {"name": "CritiqueAgent"}

        pipeline = Pipeline(mock_config)
        agent_names = [a["name"] for a in pipeline.get_agent_info()]
        assert "SearchAgent" in agent_names
        assert "ReaderAgent" in agent_names
        assert "WriterAgent" in agent_names
        assert "CritiqueAgent" in agent_names


def test_pipeline_execution_success(mock_config):
    with patch("pipeline.SearchAgent"), \
         patch("pipeline.ReaderAgent"), \
         patch("pipeline.WriterAgent"), \
         patch("pipeline.CritiqueAgent"):
        pipeline = Pipeline(mock_config)

        # Mock the 4 stages
        pipeline._execute_search_stage = MagicMock(return_value={
            "success": True,
            "data": {
                "results": [
                    {"title": "Result 1", "link": "https://example.com/1"},
                    {"title": "Result 2", "link": "https://example.com/2"}
                ]
            }
        })
        pipeline._execute_read_stage = MagicMock(return_value={
            "success": True,
            "data": {
                "scraped_contents": [{"url": "https://example.com/1", "content": "Text 1"}]
            }
        })
        pipeline._execute_write_stage = MagicMock(return_value={
            "success": True,
            "data": {"report": "# Full Research Report\n\n## Executive Summary\nAll good."}
        })
        pipeline._execute_critique_stage = MagicMock(return_value={
            "success": True,
            "data": {
                "feedback": "Score: 9/10. Pass.",
                "is_approved": True,
                "overall_score": 9
            }
        })

        result = pipeline.execute("AI Robotics", num_search_results=2, max_pages_to_read=1, save_results=False)

        assert result["success"] is True
        assert result["topic"] == "AI Robotics"
        assert result["final_report"] is not None
        assert result["is_approved"] is True
        assert result["critique_score"] == 9
        assert result["stages"]["search"]["success"] is True
        assert result["stages"]["read"]["success"] is True
        assert result["stages"]["write"]["success"] is True
        assert result["stages"]["critique"]["success"] is True


def test_pipeline_search_failure_halts_flow(mock_config):
    with patch("pipeline.SearchAgent"), \
         patch("pipeline.ReaderAgent"), \
         patch("pipeline.WriterAgent"), \
         patch("pipeline.CritiqueAgent"):
        pipeline = Pipeline(mock_config)

        pipeline._execute_search_stage = MagicMock(return_value={
            "success": False,
            "error": "SerpAPI rate limit exceeded",
            "data": None
        })

        result = pipeline.execute("Quantum AI", save_results=False)

        assert result["success"] is False
        assert result["error"] == "Search stage failed"
        assert result["stages"]["read"] is None
        assert result["stages"]["write"] is None
