from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_api_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


def test_api_research_endpoint():
    mock_pipeline_result = {
        "success": True,
        "topic": "Neuromorphic Computing",
        "final_report": "# Neuromorphic Computing Report\n\nExecutive summary...",
        "critique_feedback": "Score: 9/10. Pass.",
        "is_approved": True,
        "critique_score": 9,
        "error": None,
        "timestamp": "2026-10-07T12:00:00"
    }

    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = mock_pipeline_result

    with patch("api.get_pipeline", return_value=mock_pipeline):
        response = client.post("/research", json={
            "topic": "Neuromorphic Computing",
            "num_results": 3,
            "max_pages": 2
        })

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["topic"] == "Neuromorphic Computing"
    assert res_data["is_approved"] is True
    assert res_data["critique_score"] == 9
    assert "Neuromorphic Computing Report" in res_data["final_report"]


def test_api_research_invalid_topic():
    response = client.post("/research", json={
        "topic": "a",  # min_length is 3
        "num_results": 3,
        "max_pages": 2
    })
    assert response.status_code == 422
