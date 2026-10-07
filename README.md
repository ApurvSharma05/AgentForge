# AgentForge — AI Multi-Agent Research & Report Generation System

> **An intelligent multi-agent framework that searches, reads, critiques, and writes — transforming scattered internet information into structured, high-quality research reports.**

Built for modern research workflows, **AgentForge** combines multiple AI agents that collaborate like a real research team.

Instead of relying on a single AI model to do everything, AgentForge divides responsibilities across specialized agents, improving clarity, scalability, and output quality.

---

# Why AgentForge?

Research is rarely a linear process. Finding reliable information often requires navigating multiple sources, filtering noise, organizing scattered insights, and transforming raw information into something structured and meaningful.

AgentForge simplifies this workflow by dividing the research lifecycle into specialized AI responsibilities.

Instead of depending on a single model to search, read, reason, summarize, and evaluate everything at once, AgentForge distributes these tasks across multiple agents that work together. Each agent focuses on one responsibility, creating a more organized, explainable, and reliable research pipeline.

This architecture improves consistency while making outputs easier to validate and extend.

---

# The Problem We Solve

Large Language Models are powerful, but they often struggle when asked to:

* Research deeply
* Validate sources
* Process multiple webpages
* Organize information logically
* Self-evaluate quality

Most AI outputs are generated in a single pass.

**AgentForge introduces collaborative intelligence.**

Instead of one AI doing everything, multiple specialized agents work together efficiently.

---

# What Makes AgentForge Different?

### Traditional AI Workflow

```text
User → One Prompt → One Response
```

### AgentForge Workflow

```text
User Query
    ↓
Search Agent → Finds relevant sources
    ↓
Reader Agent → Extracts useful content
    ↓
Writer Agent → Generates structured report
    ↓
Critique Agent → Improves quality
    ↓
Final Refined Output
```

This layered architecture creates:

* Better factual grounding
* Cleaner outputs
* Higher reliability
* Improved scalability
* Stronger explainability

---

# Architecture Overview

```text
┌────────────────────┐
│      User Input    │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│    Search Agent    │
│ Finds Web Sources  │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│    Reader Agent    │
│ Extracts Content   │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│    Writer Agent    │
│ Creates Report     │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│   Critique Agent   │
│ Improves Quality   │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│   Final Research   │
└────────────────────┘
```

---

# Core Features

### Multi-Agent Collaboration

AgentForge uses a role-based architecture where every agent contributes to a specific stage of the research process. This separation of responsibilities improves clarity, reduces redundancy, and creates a more structured system compared to single-prompt workflows.

### Intelligent Web Discovery

The SearchAgent identifies relevant sources from across the web using query-driven retrieval. Instead of relying on manually curated links, the system dynamically gathers resources aligned with the user's research topic.

### Structured Content Extraction

The ReaderAgent processes webpages by removing unnecessary HTML elements and extracting meaningful textual information. This ensures that downstream agents work only with clean, usable content.

### AI-Powered Report Generation

The WriterAgent transforms fragmented research into coherent reports with organized sections, summaries, and references. The goal is not only generation but readability and logical flow.

### Quality Assurance Through Critique

The CritiqueAgent acts as a validation layer. It reviews generated outputs to identify weak structure, missing context, or incomplete analysis before the final response is delivered.

### Modular and Extensible Design

Each component functions independently, allowing developers to extend the system by adding new agents, replacing APIs, or integrating alternative workflows without redesigning the entire architecture.

---

# Project Structure

```bash
agentforge/
│
├── base_agent.py             # Shared abstract base class for all agents
├── search_agent.py           # SerpAPI search agent with tenacity exponential backoff
├── reader_agent.py           # BeautifulSoup scraping agent with parallel ThreadPoolExecutor
├── writer_agent.py           # Groq Llama-3.3-70B report drafting agent with token cost guard
├── critique_agent.py         # Structured Pydantic critique agent with 1-10 quality rubric
├── pipeline.py               # Orchestrator managing sequential execution and logging
├── agent_manager.py          # Dynamic agent registry and lifecycle manager
├── api.py                    # FastAPI REST serving layer (/health, /research)
├── app.py                    # Dark-themed Streamlit interactive web application
├── config.py                 # Configuration and environment variable loader
├── utils.py                  # Shared helpers for logging, formatting, and file export
├── tests/                    # Comprehensive unit and integration test suite (21 tests)
│   ├── test_search_agent.py
│   ├── test_reader_agent.py
│   ├── test_writer_agent.py
│   ├── test_critique_agent.py
│   ├── test_pipeline.py
│   └── test_api.py
├── eval/                     # Evaluation benchmark suite with golden topics
│   └── run_eval.py
├── Dockerfile                # Production container deployment definition
├── requirements_minimal.txt  # Curated, lightweight dependencies list
├── requirements.txt          # Full locked environment dependencies
├── .env.example              # Template environment variables (safe for version control)
└── README.md                 # System documentation
```

---

# Meet The Agents

## BaseAgent

The foundation layer.

Every agent inherits from this class to maintain consistent structure.

### Responsibilities

* Shared execution workflow
* Input validation
* Error handling
* Unified response formatting

---

## SearchAgent

The researcher of the system.

SearchAgent explores the web and finds useful resources based on user queries.

### Responsibilities

* Internet search
* URL collection
* Metadata retrieval
* Query processing

### Powered By

* SerpAPI

---

## ReaderAgent

The reader of the team.

ReaderAgent opens webpages and extracts meaningful content.

### Responsibilities

* HTML parsing
* Content cleaning
* Text extraction
* Multi-page support

### Technologies

* requests
* BeautifulSoup

---

## WriterAgent

The storyteller.

WriterAgent transforms scattered research into structured knowledge.

### Responsibilities

* Summarization
* Report generation
* Markdown formatting
* Structured writing

### Example Output

```markdown
# Research Topic

## Overview

## Key Insights

## Findings

## References
```

---

## CritiqueAgent

The quality controller.

Before final output, CritiqueAgent reviews generated content for gaps and improvements.

### Responsibilities

* Quality checking
* Structural review
* Missing information detection
* Feedback generation

---

# Tech Stack

### Backend

* Python

### APIs

* SerpAPI
* Groq API

### Libraries

* requests
* BeautifulSoup4
* dotenv
* langchain-groq

---

# Quick Start & Installation

## 1. Clone & Set Up Environment

```bash
git clone <your-repository-url>
cd multi-agent
python -m venv venv
venv\Scripts\activate       # Windows
# or: source venv/bin/activate  # macOS / Linux
```

## 2. Install Dependencies

You can install either the curated minimal dependencies or the full locked environment:

```bash
# Curated lightweight installation (recommended):
pip install -r requirements_minimal.txt

# Or full locked dependencies:
pip install -r requirements.txt
```

## 3. Configure API Keys

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

```env
SERP_API_KEY=your_serpapi_key_here
GROQ_API_KEY=your_groq_api_key_here
LOG_LEVEL=INFO
SEARCH_TIMEOUT=15
SEARCH_MAX_RESULTS=10
```

---

# Running AgentForge

### Option A: Interactive Streamlit Web UI

```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser. Configure search depth, execute research queries, view real-time progress, read structured reports and 1-10 critique scores, and download results in Markdown or JSON format.

### Option B: FastAPI REST Serving Layer

AgentForge can be run as a headless REST microservice:

```bash
uvicorn api:app --reload --port 8000
```
Interactive Swagger documentation is auto-generated at [http://localhost:8000/docs](http://localhost:8000/docs).

- `GET /health`: Health check and system readiness
- `POST /research`: Execute research pipeline programmatically with request payload `{"topic": "...", "num_results": 5, "max_pages": 3}`

### Option C: Docker Container

Build and run the lightweight container (injecting API keys at runtime):

```bash
docker build -t agentforge .
docker run -p 8501:8501 -e SERP_API_KEY="your_key" -e GROQ_API_KEY="your_key" agentforge
```

---

# Testing & Quality Evaluation

### Automated Test Suite (pytest)

The project includes an executable 21-test suite covering all agents, edge cases, tenacity exponential retries, and API endpoints with mocked network calls:

```bash
pytest tests/ -v
```

### Reproducible Quality Evaluation (Eval Suite)

The evaluation suite benchmarks report quality against golden topics, verifying minimum length, section coverage, and critique scores:

```bash
# Run via pytest:
pytest eval/run_eval.py -v

# Or run the benchmark script directly (requires live keys):
python eval/run_eval.py
```

---

# Limitations

- **JavaScript Rendering**: Web scraping relies on BeautifulSoup and `requests`. Heavy Single-Page Applications (SPAs) built with React/Vue that render content purely via client-side JavaScript will yield minimal text.
- **Search Dependency**: Research report quality depends on Google search results indexed and retrieved via SerpAPI.
- **Hallucination Risk**: While multi-page grounding and critique significantly reduce hallucinations, LLMs can occasionally generate statements not strictly present in source texts.
- **API Rate Limits**: Subject to external rate limits from SerpAPI and Groq depending on your subscription tier.

---

# Quick Demo Workflow

```text
User asks a research question
        ↓
SearchAgent gathers resources
        ↓
ReaderAgent extracts knowledge
        ↓
WriterAgent creates report
        ↓
CritiqueAgent improves quality
        ↓
Final polished response
```

---

# Future Scope

AgentForge is designed as a foundation for larger collaborative AI systems.

Future improvements include memory-enabled agents capable of retaining long-term context, asynchronous execution for faster multi-agent processing, and direct communication between agents to improve coordination.

Additional enhancements may include knowledge graph integration, persistent storage layers, multi-document summarization, and adaptive orchestration where agents dynamically decide the next best action based on task complexity.

These additions would move AgentForge beyond a research assistant into a fully autonomous reasoning pipeline.

---

# Contribution

Contributions are welcome.

### How To Contribute

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Commit updates
5. Open a pull request

---

# License

MIT License

---

# Final Thought

AgentForge demonstrates how complex tasks become more reliable when intelligence is distributed rather than centralized.

By separating research into discovery, extraction, writing, and critique, the system mirrors how real teams collaborate, where specialization improves both quality and efficiency.

Rather than functioning as a single-response AI tool, AgentForge presents a scalable framework for building agent-driven research systems capable of producing structured, explainable, and high-quality outputs.

> Built to explore the future of collaborative AI orchestration.
