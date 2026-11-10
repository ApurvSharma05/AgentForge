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


def test_reader_backfills_failed_pages():
    agent = ReaderAgent()
    urls = [f"https://example.com/{i}" for i in range(5)]

    def fake_scrape(url):
        if url.endswith(("/0", "/1")):
            raise requests.exceptions.HTTPError("404")
        return f"content of {url}"

    # Patch _scrape_url directly so the tenacity wait is skipped.
    with patch.object(agent, "_scrape_url", side_effect=fake_scrape) as mock_scrape:
        result = agent.execute({"urls": urls, "max_pages": 3})

    assert result["success"] is True
    got = sorted(item["url"] for item in result["data"]["scraped_contents"])
    assert got == ["https://example.com/2", "https://example.com/3", "https://example.com/4"]
    assert len(result["data"]["errors"]) == 2
    assert mock_scrape.call_count == 5


def test_reader_stops_when_candidates_run_out():
    agent = ReaderAgent()
    urls = ["https://example.com/a", "https://example.com/b", "https://example.com/c"]

    def fake_scrape(url):
        if url.endswith("/a"):
            return "only good page"
        raise requests.exceptions.Timeout("boom")

    with patch.object(agent, "_scrape_url", side_effect=fake_scrape):
        result = agent.execute({"urls": urls, "max_pages": 3})

    assert result["success"] is True
    assert result["data"]["pages_processed"] == 1
    assert len(result["data"]["errors"]) == 2


def test_reader_does_not_read_more_than_needed():
    agent = ReaderAgent()
    urls = [f"https://example.com/{i}" for i in range(6)]
    with patch.object(agent, "_scrape_url", return_value="ok") as mock_scrape:
        result = agent.execute({"urls": urls, "max_pages": 2})
    assert result["data"]["pages_processed"] == 2
    assert mock_scrape.call_count == 2


def test_reader_treats_empty_text_as_failure_and_backfills():
    agent = ReaderAgent()
    urls = ["https://example.com/js-only", "https://example.com/real"]

    def fake_scrape(url):
        return "" if "js-only" in url else "real text"

    with patch.object(agent, "_scrape_url", side_effect=fake_scrape):
        result = agent.execute({"urls": urls, "max_pages": 1})

    assert [i["url"] for i in result["data"]["scraped_contents"]] == ["https://example.com/real"]
