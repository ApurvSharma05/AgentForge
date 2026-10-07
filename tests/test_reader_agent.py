from unittest.mock import MagicMock, patch
import requests
from reader_agent import ReaderAgent

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Article</title></head>
<body>
    <header><p>Site Header to Ignore</p></header>
    <nav><a href="#">Navigation Link</a></nav>
    <script>console.log("script block");</script>
    <style>body { color: red; }</style>
    <h1>Main Article Heading</h1>
    <p>This is a paragraph discussing AI agents and workflow orchestration.</p>
    <ul>
        <li>First key insight</li>
        <li>Second key insight</li>
    </ul>
    <footer><p>Copyright 2026</p></footer>
</body>
</html>
"""


def test_reader_valid_input_and_cleaning():
    agent = ReaderAgent()
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_HTML
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = agent.execute({"urls": ["https://example.com/article1"], "max_pages": 1})

    assert result["success"] is True
    assert result["data"]["pages_processed"] == 1
    content = result["data"]["scraped_contents"][0]["content"]
    assert "Main Article Heading" in content
    assert "This is a paragraph discussing AI agents" in content
    assert "First key insight" in content
    # Ensure stripped elements are excluded
    assert "script block" not in content
    assert "Copyright 2026" not in content
    assert "Site Header" not in content


def test_reader_parallel_scraping():
    agent = ReaderAgent(config={"max_workers": 3})
    urls = [f"https://example.com/page{i}" for i in range(3)]

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_HTML
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = agent.execute({"urls": urls, "max_pages": 3})

    assert result["success"] is True
    assert result["data"]["pages_processed"] == 3
    assert len(result["data"]["scraped_contents"]) == 3


def test_reader_invalid_input():
    agent = ReaderAgent()
    # Missing 'urls'
    res1 = agent.execute({"invalid_key": "val"})
    assert res1["success"] is False

    # 'urls' is not a list
    res2 = agent.execute({"urls": "https://single-url.com"})
    assert res2["success"] is False


def test_reader_retry_on_network_failure():
    agent = ReaderAgent()
    with patch("requests.get") as mock_get:
        mock_ok = MagicMock()
        mock_ok.text = "<p>Recovered content</p>"
        mock_ok.raise_for_status.return_value = None

        mock_get.side_effect = [
            requests.exceptions.Timeout("Connection timed out"),
            mock_ok
        ]

        result = agent.execute({"urls": ["https://example.com/timeout"], "max_pages": 1})

    assert result["success"] is True
    assert "Recovered content" in result["data"]["scraped_contents"][0]["content"]
    assert mock_get.call_count == 2
