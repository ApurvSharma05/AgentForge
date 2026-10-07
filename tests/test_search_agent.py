from unittest.mock import MagicMock, patch
import requests
from search_agent import SearchAgent

MOCK_SERP_RESPONSE = {
    "organic_results": [
        {
            "title": "Quantum Computing Basics",
            "link": "https://example.com/quantum",
            "snippet": "An introduction to quantum superposition and qubits.",
            "position": 1,
        },
        {
            "title": "Quantum Algorithms in 2026",
            "link": "https://example.com/algorithms",
            "snippet": "Overview of Shor's and Grover's algorithms.",
            "position": 2,
        },
    ]
}


def test_search_valid_query():
    agent = SearchAgent(api_key="test_serp_key")
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_SERP_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = agent.execute({"query": "quantum computing", "num_results": 2})

    assert result["success"] is True
    assert result["data"]["num_results"] == 2
    assert len(result["data"]["results"]) == 2
    assert result["data"]["results"][0]["title"] == "Quantum Computing Basics"
    assert result["data"]["metadata"]["query"] == "quantum computing"


def test_search_missing_query():
    agent = SearchAgent(api_key="test_serp_key")
    result = agent.execute({"invalid_field": "test"})
    assert result["success"] is False
    assert "Invalid input" in result["error"]


def test_search_empty_query():
    agent = SearchAgent(api_key="test_serp_key")
    result = agent.execute({"query": "   "})
    assert result["success"] is False
    assert "Invalid input" in result["error"]


def test_search_retry_on_network_error():
    agent = SearchAgent(api_key="test_serp_key")
    with patch("requests.get") as mock_get:
        mock_ok = MagicMock()
        mock_ok.json.return_value = MOCK_SERP_RESPONSE
        mock_ok.raise_for_status.return_value = None

        # Fail twice with ConnectionError, then succeed on 3rd attempt
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Temporary network glitch"),
            requests.exceptions.ConnectionError("Temporary network glitch"),
            mock_ok,
        ]

        result = agent.execute({"query": "quantum computing", "num_results": 2})

    assert result["success"] is True
    assert mock_get.call_count == 3
    assert len(result["data"]["results"]) == 2


def test_batch_search():
    agent = SearchAgent(api_key="test_serp_key")
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_SERP_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        batch_result = agent.batch_search(["query1", "query2"])

    assert batch_result["success"] is True
    assert batch_result["total_queries"] == 2
    assert batch_result["successful"] == 2
