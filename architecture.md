# Multi-Agent Research System - Architecture

![System Architecture Diagram](Multi%20Research%20Agentic%20AI.png)

An AI-powered research automation system that utilizes a sequential pipeline of specialized intelligent agents to transform a research topic into a comprehensive, evaluated report.

## 🏗️ System Overview

The system is built on a modular architecture consisting of a user interface, a pipeline orchestrator, and a suite of specialized agents. Each agent is responsible for a specific stage of the research lifecycle, ensuring high-quality, structured, and actionable outputs.

---

## 🛠️ Tech Stack

- **Core Logic:** Python
- **Framework:** LangChain
- **Web Interface:** Streamlit
- **LLM Provider:** Groq (Llama-3.3-70B)
- **Data Extraction:** BeautifulSoup, Requests
- **Search Engine:** SerpAPI (Google Search)

---

## 🧩 Architectural Components

### 1. User Interface (Streamlit Application)
Provides a web-based portal where users can:
- Enter research topics.
- Configure search and model parameters.
- Monitor real-time progress.
- Download the final research report.

### 2. Pipeline Orchestrator (`pipeline.py`)
The central engine that manages the sequential execution of the research workflow: **Search → Read → Write → Critique**.
- **Workflow Management:** Controls the transition between stages.
- **Stage Tracking:** Monitors the status of each agent.
- **Error Handling:** Manages exceptions and external service timeouts.
- **Result Aggregation:** Consolidates outputs from all agents into the final report.

### 3. Agent Manager (`agent_manager.py`)
A registry service that initializes, manages, and provides the Orchestrator with access to the individual agents.

---

## 🤖 Agent Breakdown

| Agent | Responsibility | Key Tools | Output |
| :--- | :--- | :--- | :--- |
| **SearchAgent** | Collects high-quality sources from the web. | SerpAPI | List of URLs, titles, and snippets. |
| **ReaderAgent** | Scrapes and extracts relevant text from URLs. | BeautifulSoup | Clean, structured text content. |
| **WriterAgent** | Synthesizes information into a report. | Groq LLM | Structured Markdown report. |
| **CritiqueAgent** | Evaluates the report for quality and depth. | Groq LLM | Feedback, suggestions, and score (1-10). |

---

## 🔄 Data Flow (Sequential)

1. **Input:** User provides a topic via the UI.
2. **Discovery:** `SearchAgent` queries Google via SerpAPI to find authoritative sources.
3. **Extraction:** `ReaderAgent` visits the identified URLs and extracts the core textual content.
4. **Synthesis:** `WriterAgent` processes the raw text using the Groq LLM to generate a structured research paper.
5. **Evaluation:** `CritiqueAgent` reviews the report, providing a quality score and identifying areas for improvement.
6. **Output:** The final package includes the Research Report, Critique Feedback, and an overall Reliability Score.

---

## ⚙️ Configuration
The system loads sensitive credentials and environment-specific settings from a `.env` file:
- `SERP_API_KEY`
- `GROQ_API_KEY`
- Model selection and search depth settings.
- Logging levels.
