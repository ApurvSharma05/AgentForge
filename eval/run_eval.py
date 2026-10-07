"""
AgentForge Evaluation Suite.
Measures report structure, length, factual source inclusion, and critique scoring.
Run via:
    pytest eval/run_eval.py -v
    python eval/run_eval.py
"""

import os
import sys
import pytest
from config import Config
from pipeline import Pipeline

# Golden topics for benchmarking
GOLDEN_DATASET = [
    {
        "topic": "Python asyncio event loop architecture",
        "min_words": 800,
        "required_sections": ["Executive Summary", "Key Findings", "References"]
    },
    {
        "topic": "Retrieval-Augmented Generation best practices 2026",
        "min_words": 800,
        "required_sections": ["Executive Summary", "Technical Deep Dive", "Recommendations"]
    }
]


def has_live_api_keys() -> bool:
    """Check if valid API keys exist for live integration evaluation."""
    serp = os.getenv("SERP_API_KEY", "")
    groq = os.getenv("GROQ_API_KEY", "")
    return bool(serp and not serp.startswith("your_") and groq and not groq.startswith("your_"))


@pytest.fixture(scope="module")
def pipeline():
    if not has_live_api_keys():
        pytest.skip("Skipping live eval tests: valid live API keys not set in environment.")
    config = Config()
    return Pipeline(config)


@pytest.mark.integration
def test_report_has_required_sections(pipeline):
    topic_data = GOLDEN_DATASET[0]
    result = pipeline.execute(
        topic=topic_data["topic"],
        num_search_results=3,
        max_pages_to_read=2,
        save_results=False
    )
    assert result["success"], f"Pipeline failed: {result.get('error')}"
    report = result["final_report"]
    assert report is not None
    for section in topic_data["required_sections"]:
        assert section.lower() in report.lower(), f"Missing required section: {section}"


@pytest.mark.integration
def test_report_minimum_length(pipeline):
    topic_data = GOLDEN_DATASET[0]
    result = pipeline.execute(
        topic=topic_data["topic"],
        num_search_results=3,
        max_pages_to_read=2,
        save_results=False
    )
    assert result["success"], f"Pipeline failed: {result.get('error')}"
    word_count = len(result["final_report"].split())
    assert word_count >= topic_data["min_words"], f"Report too short: {word_count} words (min {topic_data['min_words']})"


@pytest.mark.integration
def test_search_returns_results(pipeline):
    result = pipeline.execute(
        topic="machine learning basics",
        num_search_results=3,
        max_pages_to_read=1,
        save_results=False
    )
    assert result["stages"]["search"]["data"]["num_results"] >= 1


def run_benchmark():
    """CLI runner for direct evaluation invocation."""
    print("=" * 60)
    print("AgentForge Live Quality Benchmark")
    print("=" * 60)

    if not has_live_api_keys():
        print("Error: SERP_API_KEY and GROQ_API_KEY must be set in .env to run live benchmarks.")
        sys.exit(1)

    config = Config()
    pipe = Pipeline(config)

    for item in GOLDEN_DATASET:
        print(f"\nEvaluating: '{item['topic']}'...")
        res = pipe.execute(item["topic"], num_search_results=3, max_pages_to_read=2, save_results=False)
        if not res["success"]:
            print(f"FAILED: {res.get('error')}")
            continue

        report = res["final_report"] or ""
        words = len(report.split())
        score = res.get("critique_score", "N/A")
        approved = res.get("is_approved", False)

        print(f"  Words: {words} (Threshold: {item['min_words']})")
        print(f"  Critique Score: {score}/10 | Approved: {approved}")
        for s in item["required_sections"]:
            found = s.lower() in report.lower()
            print(f"  Section '{s}': {'✓' if found else '✗'}")


if __name__ == "__main__":
    run_benchmark()
