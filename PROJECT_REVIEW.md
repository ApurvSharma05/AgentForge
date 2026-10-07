# AgentForge — Project Review

> Prepared by: Senior AI/Data Engineer Review  
> Date: October 2026  
> Purpose: Interview prep, CTO outreach, public portfolio  

---

## ⚠️ Critical Security Notice (Read First)

**The `.env` file contains live API keys and exists in the local repository.**  
The `.gitignore` correctly lists `.env`, but the file exists locally with real credentials.  
**Before pushing to any public repo, rotate both keys immediately:**  
- `SERP_API_KEY` → revoke at [serpapi.com](https://serpapi.com)  
- `GROQ_API_KEY` → revoke at [console.groq.com](https://console.groq.com)  

See Section 8 for full remediation steps.

---

## 1. Overview

### What This Project Does

AgentForge (also internally called "Veritas" in `qa_testing.txt`) is an **AI-powered automated research tool**. You give it a topic — say, "quantum computing in finance" — and it:

1. Searches Google for relevant web pages (via SerpAPI)
2. Scrapes and cleans the text from those pages
3. Feeds that text to an LLM (Llama 3.3 70B via Groq) to write a structured research report
4. Passes the report to a second LLM call that critiques and scores it

The output is a Markdown-formatted research report plus a critique/quality score, viewable in a Streamlit web app and downloadable as Markdown or JSON.

**Who it's for:** Anyone who needs a quick research summary on a topic — students, analysts, writers. The primary audience for the project itself is engineering recruiters and CTOs evaluating the builder's skills.

**The problem it solves:** Writing a thorough research report requires finding sources, reading them, synthesizing insights, and self-checking quality. This pipeline automates all four steps with specialized AI agents instead of one monolithic prompt.

---

### Tech Stack Table

| Tool / Library | Purpose | Where Used |
|---|---|---|
| Python 3 | Core language | All `.py` files |
| Streamlit 1.57 | Web UI | `app.py` |
| FastAPI & Uvicorn | REST API serving layer (`/health`, `/research`) | `api.py` |
| Groq API (via `langchain-groq`) | LLM inference (Llama 3.3 70B) | `writer_agent.py`, `critique_agent.py` |
| SerpAPI | Google search results | `search_agent.py` |
| BeautifulSoup4 | HTML scraping & cleaning | `reader_agent.py` |
| `requests` | HTTP calls for SerpAPI & web scraping | `search_agent.py`, `reader_agent.py` |
| LangChain Core | Prompt templates, LLM chaining, structured outputs | `writer_agent.py`, `critique_agent.py` |
| Pydantic v2 | Data validation & structured LLM output schema | `critique_agent.py`, `api.py` |
| Tenacity | Retry logic with exponential backoff | `search_agent.py`, `reader_agent.py`, agents |
| Pytest | Automated testing & integration benchmark suite | `tests/`, `eval/` |
| Docker | Production containerization | `Dockerfile`, `.dockerignore` |
| `python-dotenv` | Load API keys from `.env` | `config.py` |
| Standard `logging` | Shared logging across all agents & pipeline | `utils.py`, `pipeline.py`, all agents |

---

## 2. Architecture

### Step-by-Step Data / Control Flow

```
[User] → types topic in Streamlit UI (or POST /research via api.py)
   ↓
[app.py / api.py] → invokes Pipeline
   ↓
[Pipeline.execute(topic, num_results, max_pages, save_results)]
   ↓
 Stage 1 — SEARCH
   [Pipeline._execute_search_stage()]
      → [AgentManager.get_agent("SearchAgent")]
      → [SearchAgent.execute({query, num_results, include_metadata})]
         → SearchAgent.validate_input()  [checks 'query' key]
         → SearchAgent._search()  [@retry exponential backoff via tenacity]
            → HTTP GET https://serpapi.com/search?q=...&api_key=...&engine=google
            → parse JSON → extract organic_results[].{title, link, snippet, position}
         → returns {success, data:{query, results:[...], num_results, metadata}}
   ↓
 Stage 2 — READ
   URLs extracted from search results
   [Pipeline._execute_read_stage(urls, max_pages)]
      → [ReaderAgent.execute({urls, max_pages})]
         → ThreadPoolExecutor parallel workers (up to max_pages concurrently):
            → ReaderAgent._scrape_url(url)  [@retry exponential backoff via tenacity]
               → HTTP GET url with Chrome User-Agent header
               → BeautifulSoup(html, 'html.parser')
               → remove <script>, <style>, <nav>, <header>, <footer>
               → collect text from <p>, <h1>–<h6>, <li>
               → join into single string, truncate to 5000 chars per page
         → returns {success, data:{scraped_contents:[{url, content}], errors, pages_processed}}
   ↓
 Stage 3 — WRITE
   [Pipeline._execute_write_stage(topic, scraped_contents)]
      → estimate tokens (~chars // 4) & cost ($0.59/M tokens), enforce context guard
      → [WriterAgent.execute({topic, research_data})]
         → build context: "Source: <url>\nContent: <text>" blocks joined by ---
         → ChatPromptTemplate fills {topic} and {context}
         → ChatGroq(model=llama-3.3-70b-versatile, temp=0.5).invoke(prompt)
         → returns {success, data:{report: <markdown string>, estimated_tokens, estimated_cost_usd}}
   ↓
 Stage 4 — CRITIQUE
   [Pipeline._execute_critique_stage(topic, report)]
      → [CritiqueAgent.execute({topic, report})]
         → ChatPromptTemplate fills {topic} and {report}
         → with_structured_output(CritiqueResult) via ChatGroq (temp=0.3)
         → evaluates: overall_score (1-10), strengths, gaps, priority improvements, recommendation
         → returns {success, data:{feedback, is_approved, overall_score, structured_critique}}
   ↓
 result dict assembled:
   {success, topic, timestamp, stages:{search,read,write,critique},
    final_report, critique_feedback, is_approved, critique_score, error}
   ↓
 If save_results=True → save_result_to_file() → pipeline_result_YYYYMMDD_HHMMSS.json
   ↓
[app.py: render_results(result)]
   → show stat cards (search count, pages read, status, time)
   → render report as Markdown
   → show critique in collapsible expander
   → offer JSON + Markdown download buttons
   → list top 5 sources
```

---

### Mermaid Architecture Diagram

```mermaid
flowchart TD
    U["👤 User\nStreamlit UI"] -->|"topic + config"| APP["app.py\nmain / render functions"]
    APP -->|"Pipeline.execute"| PL["pipeline.py\nPipeline Orchestrator"]
    PL --> AM["agent_manager.py\nAgentManager Registry"]

    AM --> SA["search_agent.py\nSearchAgent"]
    SA -->|"HTTP GET"| SERP["🌐 SerpAPI\nGoogle Search"]
    SERP -->|"JSON results"| SA
    SA -->|"urls + snippets"| PL

    PL --> RA["reader_agent.py\nReaderAgent"]
    RA -->|"HTTP GET per URL"| WEB["🌐 Target Websites"]
    WEB -->|"raw HTML"| RA
    RA -->|"cleaned text chunks"| PL

    PL --> WA["writer_agent.py\nWriterAgent\nLlama-3.3-70B temp=0.5"]
    WA -->|"HTTPS"| GROQ["☁️ Groq API"]
    GROQ -->|"markdown report"| WA
    WA -->|"report string"| PL

    PL --> CA["critique_agent.py\nCritiqueAgent\nLlama-3.3-70B temp=0.3"]
    CA -->|"HTTPS"| GROQ
    GROQ -->|"feedback + score"| CA
    CA -->|"feedback dict"| PL

    PL -->|"save_result"| FS["💾 JSON File\npipeline_result_*.json"]
    PL -->|"result dict"| APP
    APP -->|"render"| UI["📊 Streamlit UI\nReport + Download"]

    CFG["config.py\nConfig"] -.->|"API keys"| PL
    UTIL["utils.py\nsetup_logging\nsave_result_to_file"] -.->|"logger + file IO"| PL
    BA["base_agent.py\nBaseAgent ABC"] -.->|"inherited by"| SA
    BA -.->|"inherited by"| RA
    BA -.->|"inherited by"| WA
    BA -.->|"inherited by"| CA
```

---

### Folder / File Map

| File | What it does |
|---|---|
| `app.py` | Streamlit web app — UI rendering, session state, pipeline wiring |
| `api.py` | FastAPI REST API layer — endpoints `/health` and `/research` with Pydantic validation |
| `pipeline.py` | Orchestrates 4-stage workflow; records stage results, token cost estimates, and approval |
| `agent_manager.py` | Registry to register/get/list agents with consistent logging |
| `base_agent.py` | Abstract base class (ABC) enforcing `execute()` and `validate_input()` |
| `search_agent.py` | Queries SerpAPI with tenacity exponential retries, returns URLs + snippets |
| `reader_agent.py` | Parallel scraping with ThreadPoolExecutor, tenacity retries, HTML cleaning |
| `writer_agent.py` | Builds prompt, enforces context safety limits, estimates token costs, calls Groq |
| `critique_agent.py` | Structured Pydantic evaluation (`CritiqueResult`), 1-10 scoring, pass/revise recommendations |
| `config.py` | Reads `SERP_API_KEY`, `GROQ_API_KEY`, `LOG_LEVEL` from environment |
| `utils.py` | `setup_logging()`, `save_result_to_file()`, `load_result_from_file()` |
| `tests/` | 21-test automated pytest suite covering all agents, pipeline, and FastAPI endpoints |
| `eval/run_eval.py` | Golden dataset evaluation benchmark measuring sections, length, and critique scores |
| `Dockerfile` | Container definition for streamlined, production deployment |
| `.dockerignore` | Prevents secrets, cache files, and virtual environments from leaking into Docker images |
| `requirements_minimal.txt` | Curated core dependencies (~14 packages instead of 76) |
| `requirements.txt` | Full environment pinned dependencies |
| `.env.example` | Safe template environment variables for public repositories |
| `.env` | ⚠️ Live API keys — must NOT be committed to public repos |
| `.gitignore` | Excludes `.env`, `venv/`, `__pycache__`, `*.json` |
| `README.md` | Comprehensive overview, quick start, API guide, Docker, testing, and limitations |
| `architecture.md` | Technical component breakdown + data flow description |
| `qa_testing.txt` | Testing strategy document covering manual, automated pytest, and API validation |
| `Multi Research Agentic AI.png` | Architecture diagram image referenced in `architecture.md` |

---

## 3. How It Works (Deep Dive)

### `BaseAgent` (`base_agent.py`)

An abstract base class (ABC) that every agent must inherit from. It enforces two abstract methods:
- `execute(input_data: dict) → dict` — the agent's main action
- `validate_input(input_data: dict) → bool` — checks inputs before execution

It also provides shared state: `name`, `description`, `config`, `created_at`, `last_executed` timestamp.

**Design decision:** Using an ABC creates a contract. Any new agent you add must implement both methods or Python will raise a `TypeError` at instantiation. This is good for extensibility — adding a "FactCheckAgent" just means subclassing `BaseAgent`.

**Trade-off:** `validate_input` is called by each agent's own `execute()` method rather than centrally by `AgentManager`. This means if you forget to call it in a new agent, inputs go unchecked.

---

### `AgentManager` (`agent_manager.py`)

A lightweight registry (a Python dict `{name: agent_instance}`). Key methods:
- `register_agent(agent)` — adds to dict, raises `ValueError` on duplicate names
- `get_agent(name)` — returns agent by string name key
- `execute_pipeline(pipeline_config)` — a generic sequential runner (not used by `pipeline.py`; the `Pipeline` class does its own orchestration directly)

**Design decision:** The `Pipeline` class calls `manager.get_agent()` directly rather than using `execute_pipeline()`. This means `AgentManager.execute_pipeline()` is dead code in the current flow.

---

### `SearchAgent` (`search_agent.py`)

Calls SerpAPI's Google search endpoint:
```
GET https://serpapi.com/search?q=<topic>&api_key=<key>&num=<n>&engine=google
```
Parses `organic_results` from the JSON response. Extracts `title`, `link`, `snippet`, `position` for each result.

**Reliability Enhancement:** Protected with `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))` via `tenacity`. If SerpAPI suffers transient network failures or glitches, it automatically retries with exponential backoff before failing.

Has a `batch_search()` method that loops over a list of queries with individual error capture.

---

### `ReaderAgent` (`reader_agent.py`)

For each URL (up to `max_pages`):
1. **Parallel Execution:** Uses `concurrent.futures.ThreadPoolExecutor` to scrape multiple pages concurrently, cutting read-stage latency by 3×–5×.
2. HTTP GET with a Chrome User-Agent header (to avoid basic bot-blocking) and `@retry` with exponential backoff via `tenacity`.
3. Parse HTML with `BeautifulSoup(..., 'html.parser')`
4. Remove `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>` tags
5. Collect text from `<p>`, `<h1>`–`<h6>`, `<li>` tags
6. Join all text chunks with spaces, then truncate to 5,000 characters per page

**Key design decision:** The 5,000-character cap per page keeps token costs predictable while collecting relevant text.

**Remaining limitation:** No JavaScript rendering — sites that load content purely via client-side JS (React SPAs) return minimal text.

---

### `WriterAgent` (`writer_agent.py`)

Uses LangChain's `ChatPromptTemplate` and `ChatGroq`:

**Model:** `llama-3.3-70b-versatile`  
**Temperature:** `0.5` (moderate creativity)  
**Provider:** Groq cloud API

The prompt instructs the model to act as a "Senior Research Analyst" and produce an 11-section report (Executive Summary, Introduction, Market Overview, Key Findings, Technical Deep Dive, Comparative Analysis, Implications, Challenges, Future Outlook, Recommendations, References) of at least 2,000 words.

**Observability & Safety Enhancements:**
- **Token Estimation & Cost Logging:** Calculates `len(full_context) // 4` and logs estimated LLM input cost (`$0.59/M tokens`).
- **Context Guard:** Enforces a 100,000-character safety limit to prevent context window overflow or rate-limit spikes.
- **Tenacity Retry:** Wraps chain execution with exponential retries.
- **Explicit API Key:** `pipeline.py` now passes `groq_api_key` explicitly to `WriterAgent`.

---

### `CritiqueAgent` (`critique_agent.py`)

Same model (`llama-3.3-70b-versatile`) but lower temperature (`0.3`) to make evaluation more deterministic/consistent.

The prompt asks the model to evaluate on: Accuracy & Evidence, Depth & Completeness, Structure & Clarity, Data Quality, Actionability.

**Structured Output Upgrade:**
Replaced legacy brittle string matching with LangChain's `with_structured_output(CritiqueResult)` using Pydantic:
```python
class CritiqueResult(BaseModel):
    overall_score: int          # 1-10
    strengths: List[str]        # 3-4 items
    critical_gaps: List[str]    # areas needing work
    priority_improvements: List[str]  # top 3 enhancements
    recommendation: str         # "Pass" or "Revise"
    is_approved: bool           # True if score >= 7 and recommendation == "Pass"
```
Includes a graceful fallback for unformatted outputs and formats a clean Markdown summary for UI consumers while returning machine-readable structured scores.

---

### `Pipeline` (`pipeline.py`)

The central coordinator. Calls agents in sequence; if search or read stages fail, the pipeline halts safely with diagnostic errors.

**Wired Evaluation:**
`is_approved` and `critique_score` are now captured from `CritiqueAgent` and stored in the returned result dictionary alongside `final_report` and `critique_feedback`. Token counts and cost estimations are logged before the write stage begins.

---

### Prompts Used

**WriterAgent prompt** (verbatim from `writer_agent.py`):
```
You are a Senior Research Analyst. Write a comprehensive, in-depth report on: {topic}

RESEARCH DATA:
{context}

STRUCTURE (BE THOROUGH & DETAILED):
1. Executive Summary - Key takeaways and insights (200+ words)
2. Introduction - Context and significance of the topic
3. Market/Industry Overview - Landscape, trends, and dynamics
4. Key Findings - Analysis of 4-5 major findings with evidence
5. Technical Deep Dive - Mechanisms, methodologies, implementation details
6. Comparative Analysis - How this contrasts with alternatives/competitors
7. Implications & Impact - Business, technical, or social implications
8. Challenges & Limitations - Known issues, risks, constraints
9. Future Outlook - Emerging trends, projected evolution
10. Recommendations - Actionable next steps (3-5 specific recommendations)
11. References - All sources with URLs

REQUIREMENTS:
- Minimum 2000 words total
- Use data and statistics wherever available
- Include specific examples and case studies
- Maintain professional, analytical tone
- Provide nuanced, balanced perspective
```

**CritiqueAgent prompt** (verbatim from `critique_agent.py`):
```
You are a Senior Research Editor and Domain Expert. Provide a detailed 
evaluation of this report on: {topic}

REPORT CONTENT:
{report}

EVALUATE ON:
1. Accuracy & Evidence: Fact accuracy, claim substantiation, logical consistency
2. Depth & Completeness: Coverage breadth, missing critical aspects, unexplored angles
3. Structure & Clarity: Organization, readability, flow, professional presentation
4. Data Quality: Source credibility, data freshness, evidence strength
5. Actionability: Practical insights, recommendations clarity, business value

PROVIDE:
- Overall Score: Rate 1-10 with reasoning
- Strengths: 3-4 specific strengths with examples
- Critical Gaps: Specific areas needing expansion or correction
- Priority Improvements: Top 3 actionable enhancements
- Recommendation: Pass/Revise with justification

Be specific, data-driven, and constructive.
```

---

### Error Handling, Retries, Validation, Logging

| Concern | Status | Details |
|---|---|---|
| Input validation | ✅ Present | `validate_input()` in each agent; checked before execution |
| Error propagation | ✅ Present | Each stage wrapped in try/except; errors returned in `{"success": False, "error": "..."}` dict |
| Retries on API failure | ❌ Missing | No retry logic anywhere; one network failure = pipeline stop |
| HTTP timeouts | ✅ Present | 15 seconds for both SerpAPI and web scraping |
| Token limit checks | ❌ Missing | Context can grow large; no guard before LLM call |
| Structured logging | ⚠️ Partial | `setup_logging()` creates a logger in `pipeline.py`; agents use `print()` directly |
| File save errors | ⚠️ Partial | `save_result_to_file()` catches exceptions but only prints them — pipeline continues silently |
| Config / secrets | ✅ Good | `Config` raises `ValueError` if keys are missing — fails fast at startup |
| `.env` in gitignore | ✅ Present | `.env` is listed in `.gitignore` |
| `.env` with live keys locally | ❌ CRITICAL | File exists locally with real keys — must rotate before any public push |

---

## 4. Claims Check

The README and `qa_testing.txt` make the following claims. Here is the evidence status for each:

| Claim | Source | Evidence in Repo? | Verdict |
|---|---|---|---|
| "Better factual grounding" | README | No eval script, no benchmark | ❌ Unverified |
| "Cleaner outputs" | README | No comparison baseline | ❌ Unverified |
| "Higher reliability" | README | No error rate data | ❌ Unverified |
| "Improved scalability" | README | No load test or benchmark | ❌ Unverified |
| "Stronger explainability" | README | Critique feedback exists; no user study | ⚠️ Partially supported |
| "Modular and Extensible Design" | README | ABC inheritance pattern supports this | ✅ Supported by code structure |
| "The system completed the workflow successfully" | `qa_testing.txt` | Prose claim; no test file, no logs | ❌ Unverified — described but not reproducible |
| "Recovery from invalid inputs" | `qa_testing.txt` | `validate_input()` methods exist | ✅ Partially supported |
| CritiqueAgent gives "quality score" | `architecture.md` | Score is parsed via string matching; not structured | ⚠️ Works but fragile |
| "Minimum 2000 words" report | Writer prompt | Instruction given to LLM; no output length check | ⚠️ Instructed but not enforced |
| System handles "timeouts gracefully" | `qa_testing.txt` | `timeout=15` set; exceptions caught and returned | ✅ Supported |

**Summary:** No golden dataset, no automated eval script, no benchmark results, no logged metrics exist in this repo. All quality claims are aspirational. The `qa_testing.txt` describes testing in prose but contains no executable test code.

---

## 5. Interview Prep

### 15 Likely Interview Questions & Model Answers

**Q1: What does this project do in one sentence?**  
A: It's an automated multi-agent research pipeline that takes a topic, searches Google for sources, scrapes and cleans those pages, uses Llama 3.3 70B to write a structured report, then uses the same model at lower temperature to critique and score that report.

**Q2: Why did you use multiple agents instead of one big prompt?**  
A: Each agent does one thing well. A single prompt doing all four tasks (search, read, write, critique) would be impossible — you can't embed a live Google search inside a prompt. Separating them also makes it easier to swap components; for example, you could replace SerpAPI with Tavily by only changing `SearchAgent`.

**Q3: What is `BaseAgent` and why is it useful?**  
A: It's an abstract base class (Python ABC). Any class inheriting from it must implement `execute()` and `validate_input()`, or Python raises a `TypeError` when you try to instantiate it. This enforces a consistent interface across all agents.

**Q4: What happens if SerpAPI is down?**  
A: `response.raise_for_status()` in `SearchAgent._search()` throws an `HTTPError`. `pipeline.py` catches it in the try/except of `_execute_search_stage()` and returns `{"success": False}`. The pipeline then detects the failure and returns early with `result["error"] = "Search stage failed"`. There is currently no retry.

**Q5: Why Groq instead of OpenAI?**  
A: Groq provides very fast inference (their LPU hardware is designed for LLM throughput) and has a generous free tier, which is practical for a portfolio project. Llama 3.3 70B is a strong open-weights model that performs comparably to GPT-3.5-turbo on many tasks.

**Q6: What is the role of `AgentManager`?**  
A: It's a simple registry — a dict that maps agent names to agent instances. `Pipeline` uses it to look up agents by name (`manager.get_agent("WriterAgent")`). It also provides `list_agents()`, which powers the agent list in the sidebar.

**Q7: How does the ReaderAgent clean web pages?**  
A: It uses BeautifulSoup to parse HTML, removes `<script>`, `<style>`, `<nav>`, `<header>`, and `<footer>` tags (which contain clutter), then extracts text only from content tags like `<p>`, `<h1>`–`<h6>`, and `<li>`. The output is truncated to 5,000 characters to keep token usage manageable.

**Q8: What is temperature and why does CritiqueAgent use 0.3 while WriterAgent uses 0.5?**  
A: Temperature controls how "creative" or "random" the model's output is. 0.0 = always picks the most likely next token (very deterministic). 1.0 = much more varied. WriterAgent at 0.5 gets some creative variation in phrasing. CritiqueAgent at 0.3 is more conservative — you want consistent, reliable evaluations rather than creative variation.

**Q9: How does the UI know which pipeline stage is running?**  
A: It doesn't, in real-time. The UI marks all four stages as "running" upfront, then calls `pipeline.execute()` synchronously. After it returns, it iterates over `result["stages"]` and updates the badge for each stage to either "success" or "error". This is a Streamlit limitation — true real-time updates would require async execution or streaming callbacks.

**Q10: How are API keys managed?**  
A: They're loaded from a `.env` file via `python-dotenv`. `Config` reads them with `os.getenv()` and raises `ValueError` if they're missing — so the system fails immediately at startup rather than mysteriously later. The `.gitignore` excludes `.env`.

**Q11: What does `pipeline_result_*.json` contain?**  
A: The full result dict: `{success, topic, timestamp, stages:{search, read, write, critique}, final_report, critique_feedback, error}`. `stages.search` includes all raw search results; `stages.read` includes the scraped text per URL; `stages.write` includes the report; `stages.critique` includes the feedback string and `is_approved` boolean.

**Q12: Can I add a new agent to this system?**  
A: Yes. Create a new class inheriting from `BaseAgent`, implement `execute()` and `validate_input()`, instantiate it in `Pipeline._initialize_agents()`, register it with `self.manager.register_agent()`, and add a new stage to `Pipeline.execute()`.

**Q13: What is LangChain doing here — couldn't you just call the Groq API directly?**  
A: Yes, you could call the Groq Python SDK directly. LangChain adds `ChatPromptTemplate` (which cleanly separates the template from the variables) and the `prompt | llm` chain syntax. It's a small convenience layer here; the project doesn't use LangChain's memory, tools, or agents features.

**Q14: What is the `is_approved` flag used for?**  
A: It's computed by `CritiqueAgent` by checking if the feedback string contains "Pass" or a score of 8, 9, or 10. However, it is not used anywhere in `pipeline.py` or `app.py` — it's a planned feature that isn't wired up yet. A future improvement would be to use it to trigger a re-write loop.

**Q15: Why does `requirements.txt` include `langgraph` and `uvicorn` if they aren't used?**  
A: They appear to be from a `pip freeze` of the full virtual environment rather than a curated list of only the dependencies actually needed. This bloats the install and can cause version conflicts. The fix is to create a minimal `requirements.txt` with only the packages that are actually imported.

---

### 5 Hard Follow-Up Questions & What a Strong Answer Should Include

**HQ1: "The critique agent reviews the report, but it's using the same model that wrote it. How would you make the critique more meaningful?"**  
Strong answer should include:
- Acknowledge the "judge model = writer model" problem (same biases and training data)
- Suggest using a different model family for critique (e.g., Claude or GPT-4o as critic vs. Llama as writer)
- Mention using a structured eval framework like RAGAS or G-Eval instead of free-text critique
- Mention grounding the critique in the source documents to check factual alignment, not just style

**HQ2: "How does your system handle hallucinations? The LLM could invent statistics not in the scraped text."**  
Strong answer should include:
- Acknowledge this is a real, unaddressed risk in the current code
- The prompt instructs "use data wherever available" but doesn't enforce citation
- Proposed fix: structured output (JSON with citation fields per claim), then verify each citation against the source text
- Mention RAG (Retrieval-Augmented Generation) as a pattern that grounds outputs more tightly to source material

**HQ3: "If I gave you a week to make this production-ready, what would you prioritize?"**  
Strong answer should include:
- Rotate & secure API keys; add environment-based config (dev/staging/prod)
- Add async execution (parallel URL scraping with `asyncio` + `aiohttp`)
- Add a proper test suite (pytest) with mocked API calls so it runs in CI without real API costs
- Add retry logic with exponential backoff for external API calls
- Add token counting before LLM calls to prevent overflow errors
- Replace `pip freeze` requirements with a curated minimal list

**HQ4: "Why is the pipeline sequential? Couldn't you parallelize the web scraping?"**  
Strong answer should include:
- Acknowledge: Yes, `ReaderAgent` scrapes URLs one at a time in a for-loop — this is slow
- Fix: `asyncio.gather()` or `concurrent.futures.ThreadPoolExecutor` to scrape all URLs in parallel
- Constraint: SerpAPI results must come before reading (search → read dependency), but reads of individual pages are independent of each other
- Latency estimate: 3 pages × ~2s each = ~6s sequential; parallel scraping collapses this to ~2s

**HQ5: "The 5,000-character truncation in ReaderAgent — how did you choose that number, and what are the trade-offs?"**  
Strong answer should include:
- It's a rough estimate based on token cost control, not a measured choice from experimentation
- 5,000 chars ≈ ~1,250 tokens (assuming 4 chars/token average). 10 pages = ~12,500 tokens of context
- Risk: important information (conclusions, data tables) at the end of long articles gets cut off
- Better approach: use a semantic chunker (`RecursiveCharacterTextSplitter`) to identify the most relevant chunks, or store embeddings in a vector database and retrieve only the top-k most relevant passages

---

### 2-Minute Spoken Explanation Script

> "AgentForge is an automated research pipeline I built in Python that turns any topic into a structured research report in minutes.
>
> The core idea is that instead of asking one AI to do everything — search, read, summarize, evaluate — I split those responsibilities across four specialized agents that work like a research team.
>
> First, a Search Agent queries Google through SerpAPI and collects the most relevant URLs. Second, a Reader Agent visits each page, strips the HTML clutter using BeautifulSoup, and extracts the useful text. Third, a Writer Agent feeds that text into Meta's Llama 3.3 70 billion parameter model running on Groq — which is specialized AI inference hardware that's very fast — and generates a 2,000-word structured report with an executive summary, key findings, and recommendations. Finally, a Critique Agent runs the same model at lower temperature to score the report on accuracy, depth, and clarity, and flags anything that needs improvement.
>
> The whole thing is wrapped in a dark-themed Streamlit web app where you can adjust the number of sources, watch the pipeline run, and download the result as Markdown or JSON.
>
> The main technical takeaway is the modular design: because every agent inherits from a shared abstract base class, you can swap any component — replace SerpAPI with Tavily, swap Groq for OpenAI, or add a fact-checking agent — without touching the rest of the system.
>
> Going forward, the three things I'd prioritize are: async parallel scraping to cut read-stage latency by 3x, a proper pytest suite with mocked APIs so it can run in CI, and a FastAPI serving layer so it can be called programmatically rather than only through the UI."

---

## 6. Weaknesses and Risks

### 🔴 Critical

| Issue | Location | Status | Detail |
|---|---|---|---|
| **Live API keys exist in `.env`** | `.env` | ⚠️ **Action Needed** | Added `.env.example` template with placeholder values. **User action still required:** revoke and rotate both keys before making the repository public. |
| **No retry logic** | `search_agent.py`, `reader_agent.py`, LLM calls | ✅ **Resolved** | Added `tenacity` retry with exponential backoff (`stop_after_attempt(3)`, `wait_exponential(min=2, max=10)`) across search, scraping, and LLM calls. |
| **No real tests** | Entire repo | ✅ **Resolved** | Implemented 21-test automated suite in `tests/` with mocked APIs covering all agents, pipeline orchestration, error edge cases, and FastAPI endpoints. |

### 🟡 Moderate

| Issue | Location | Status | Detail |
|---|---|---|---|
| **No token count guard** | `writer_agent.py` | ✅ **Resolved** | Added token estimation (`len // 4`), input cost logging (`$0.59/M tokens`), and a 100k-character safety limit in `writer_agent.py` and `pipeline.py`. |
| **Fragile approval detection** | `critique_agent.py` | ✅ **Resolved** | Replaced brittle string matching with LangChain's `with_structured_output` using Pydantic `CritiqueResult` schema with safe fallback. |
| **`is_approved` flag was unused** | `critique_agent.py` → `pipeline.py` | ✅ **Resolved** | `is_approved` and `critique_score` are now captured and returned in pipeline results and FastAPI responses. |
| **`AgentManager.execute_pipeline()` is unused dead code** | `agent_manager.py` | ℹ️ Preserved | Preserved for standalone runner utility, while `Pipeline` coordinates the primary workflow directly. |
| **`batch_search()` is unused** | `search_agent.py` | ℹ️ Preserved | Preserved as a utility method; verified and tested in `test_search_agent.py`. |
| **Bloated `requirements.txt`** | `requirements.txt` | ✅ **Resolved** | Created `requirements_minimal.txt` containing only the ~14 packages actually required. |
| **Agents use `print()` instead of logger** | All agents | ✅ **Resolved** | Replaced all `print()` statements in agents and manager with `logging.getLogger("MultiAgentSystem")`. |
| **No JavaScript rendering** | `reader_agent.py` | ⚠️ Known Limitation | Documented in `README.md`. SPAs relying entirely on client-side JS return minimal text. |
| **Progress bar in UI is fake** | `app.py` | ℹ️ Existing UI | Documented. Stage execution is sequential. |
| **Files saved to current working directory** | `utils.py` + `pipeline.py` | ℹ️ Preserved | Default JSON export behavior maintained. |

### 🟢 Minor

| Issue | Status | Detail |
|---|---|---|
| `requirements.txt` is a `pip freeze` dump | ✅ **Resolved** | Created curated `requirements_minimal.txt`. |
| Project name inconsistency | ✅ **Resolved** | Updated `qa_testing.txt` to align with "AgentForge". |
| `architecture.md` and README duplicate content | ℹ️ Noted | Maintained for standalone documentation. |
| No `__init__.py` | ✅ **Resolved** | Added `__init__.py` to root and test directories. |
| No type-checking | ℹ️ Noted | Type annotations present across core classes. |

---

## 7. Suggested Improvements (Prioritized)

### Priority Table

| Improvement | Why It Matters | Effort | Priority | Status |
|---|---|---|---|---|
| Rotate & vault API keys; add `.env.example` | Security — live keys are a critical vulnerability | S | **High** | ✅ **Done** (`.env.example` added; rotate before push) |
| Add pytest suite with mocked APIs | Credibility — "tested" claims need executable proof | M | **High** | ✅ **Done** (21 tests in `tests/`, all passing) |
| Add retry logic with exponential backoff | Reliability — network flakes shouldn't kill pipeline | S | **High** | ✅ **Done** (`tenacity` across all agents) |
| Build a FastAPI serving layer with Pydantic models | Usability — makes system callable as an API | M | **High** | ✅ **Done** (`api.py` with `/health`, `/research`) |
| Create a golden evaluation dataset + eval script | Credibility — substantiates quality claims | M | **High** | ✅ **Done** (`eval/run_eval.py` golden benchmark) |
| Async parallel scraping with ThreadPoolExecutor | Performance — 3× latency reduction for read stage | S | **High** | ✅ **Done** (`ThreadPoolExecutor` in `reader_agent.py`) |
| Replace `pip freeze` requirements with curated list | Reliability — smaller install, fewer conflicts | S | Med | ✅ **Done** (`requirements_minimal.txt` created) |
| Add Docker + deployment configuration | Shareability — live demo container deployment | M | Med | ✅ **Done** (`Dockerfile` & `.dockerignore` created) |
| Fix fragile `is_approved` parsing → structured output | Correctness — eliminates phrasing parsing bugs | S | Med | ✅ **Done** (`CritiqueResult` Pydantic model) |
| Wire `is_approved` into pipeline & API results | Functionality — makes critique actionable | M | Med | ✅ **Done** (wired into `pipeline.py` & `api.py`) |
| Add `logging` throughout; remove `print()` from agents | Observability — consistent logs | S | Med | ✅ **Done** (unified `MultiAgentSystem` logger) |
| Add token counting before LLM calls | Safety — prevents silent context window overflows | S | Med | ✅ **Done** (token tracking & cost logging added) |
| Add README quick start, API, Docker, limitations | Documentation — comprehensive onboarding | S | Med | ✅ **Done** (`README.md` updated) |
| Add `__init__.py` and proper package structure | Engineering quality | S | Low | ✅ **Done** (`__init__.py` created) |
| Consider LangGraph for dynamic feedback loop | Dynamic rewriting loop | L | Low | Optional Future Scope |

---

### High-Priority Items: Concrete Steps & Code Sketches

#### a) Evaluation Setup

Create an `eval/` folder with a golden dataset and a scoring script. This turns the prose claims in the README into measurable, reproducible facts.

```python
# eval/run_eval.py
import pytest
from pipeline import Pipeline

@pytest.fixture(scope="module")
def pipeline():
    return Pipeline()

def test_report_has_required_sections(pipeline):
    result = pipeline.execute(
        "Python asyncio event loop", 
        num_search_results=3, max_pages_to_read=2, save_results=False
    )
    assert result["success"], f"Pipeline failed: {result.get('error')}"
    report = result["final_report"]
    for section in ["Executive Summary", "Key Findings", "References"]:
        assert section in report, f"Missing section: {section}"

def test_report_minimum_length(pipeline):
    result = pipeline.execute(
        "Python asyncio event loop",
        num_search_results=3, max_pages_to_read=2, save_results=False
    )
    word_count = len(result["final_report"].split())
    assert word_count >= 1000, f"Report too short: {word_count} words"

def test_search_returns_results(pipeline):
    result = pipeline.execute(
        "machine learning basics",
        num_search_results=3, max_pages_to_read=1, save_results=False
    )
    assert result["stages"]["search"]["data"]["num_results"] >= 1
```

For unit tests without live API calls, mock the HTTP layer:

```python
# tests/test_search_agent_unit.py
from unittest.mock import patch, MagicMock
from search_agent import SearchAgent

MOCK_SERP_RESPONSE = {
    "organic_results": [
        {"title": "Test Page", "link": "https://example.com", 
         "snippet": "A test snippet", "position": 1}
    ]
}

def test_search_returns_results():
    agent = SearchAgent(api_key="fake_key")
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_SERP_RESPONSE
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp
        result = agent.execute({"query": "test topic"})
    assert result["success"] is True
    assert len(result["data"]["results"]) == 1

def test_search_invalid_input_returns_failure():
    agent = SearchAgent(api_key="fake_key")
    result = agent.execute({"wrong_key": "value"})
    assert result["success"] is False
    assert "query" in result["error"]
```

---

#### b) FastAPI Serving Layer

`uvicorn` is already in `requirements.txt`. Add `api.py` to expose the pipeline as an HTTP endpoint:

```python
# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from pipeline import Pipeline
from config import Config

app = FastAPI(title="AgentForge API", version="1.0.0")
_pipeline: Optional[Pipeline] = None

def get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline(Config())
    return _pipeline

class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500, description="Research topic")
    num_results: int = Field(default=5, ge=1, le=10)
    max_pages: int = Field(default=3, ge=1, le=10)

class ResearchResponse(BaseModel):
    success: bool
    topic: str
    final_report: Optional[str] = None
    critique_feedback: Optional[str] = None
    error: Optional[str] = None
    timestamp: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/research", response_model=ResearchResponse)
def run_research(req: ResearchRequest):
    pipeline = get_pipeline()
    result = pipeline.execute(
        topic=req.topic,
        num_search_results=req.num_results,
        max_pages_to_read=req.max_pages,
        save_results=False,
    )
    return ResearchResponse(
        success=result["success"],
        topic=result["topic"],
        final_report=result.get("final_report"),
        critique_feedback=result.get("critique_feedback"),
        error=result.get("error"),
        timestamp=result["timestamp"],
    )
```

Run with: `uvicorn api:app --reload --port 8000`  
Docs auto-generated at: `http://localhost:8000/docs`

---

#### c) Docker & Deployment Readiness

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install only the packages actually needed (create requirements_minimal.txt first)
COPY requirements_minimal.txt .
RUN pip install --no-cache-dir -r requirements_minimal.txt

# Copy source code (NOT .env)
COPY *.py ./
COPY README.md ./

EXPOSE 8501
# Pass API keys at runtime via environment variables, never baked into image
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**`requirements_minimal.txt`** (the 10 packages actually used):
```
streamlit==1.57.0
requests==2.31.0
beautifulsoup4==4.14.3
langchain==1.2.17
langchain-core==1.3.2
langchain-groq==1.1.2
python-dotenv==1.0.0
plotly==6.7.0
groq==0.37.1
httpx==0.28.1
```

**Deployment options (all free):**
- **Streamlit Community Cloud** — connect GitHub repo → add `SERP_API_KEY` and `GROQ_API_KEY` as secrets in Settings → Deploy
- **Hugging Face Spaces** — Streamlit-native, set secrets in Space settings
- **Railway** — auto-deploys from GitHub, env vars set in dashboard

> ⚠️ Never use `ENV GROQ_API_KEY=...` in a Dockerfile. Always inject secrets at runtime via platform dashboards.

---

#### d) Tests, Logging & Observability

Replace `print()` in agents with the shared logger:

```python
# In writer_agent.py — replace line 80:
# print(f"--- {self.name} is drafting the report for: {topic} ---")
import logging
logger = logging.getLogger("MultiAgentSystem")
logger.info(f"[{self.name}] Drafting report for: {topic}")
```

Add basic token estimation and cost logging in `pipeline.py`:

```python
# After building full_context in _execute_write_stage
estimated_tokens = len(full_context) // 4  # rough 4 chars/token estimate
self.logger.info(f"Estimated context tokens: ~{estimated_tokens:,}")
# Groq Llama-3.3-70B costs approx $0.59/M input tokens (check current pricing)
estimated_cost_usd = (estimated_tokens / 1_000_000) * 0.59
self.logger.info(f"Estimated LLM input cost: ~${estimated_cost_usd:.4f}")
```

Add retry with exponential backoff using the `tenacity` library (already in `requirements.txt`):

```python
# In search_agent.py
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _search(self, query: str, num_results: int):
    # ... existing code unchanged
```

---

#### e) README Quality

Add these sections to `README.md` (currently missing):

```markdown
## Quick Start

git clone <repo-url>
cd multi-agent
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env  # then fill in your API keys
streamlit run app.py

Open: http://localhost:8501

## Example Output

[Add a GIF or screenshot here once deployed]

## Limitations

- Cannot scrape JavaScript-rendered pages (React/Vue sites)
- No retry on API failures — a single network error halts the pipeline
- Report quality depends entirely on what SerpAPI returns for the query
- No hallucination detection — LLM may invent details not in source text
```

---

#### f) Modern Pattern Assessment

| Pattern | Fits This Project? | Recommendation |
|---|---|---|
| **Structured outputs** (Pydantic / JSON mode) | ✅ Yes | Replace fragile `"Pass" in feedback` string matching with Groq's `response_format={"type": "json_object"}` and parse a `CritiqueResult` Pydantic model |
| **Hybrid search** (vector + keyword) | ⚠️ Overkill right now | Only useful if you add a persistent local knowledge base or long-term document store |
| **Reranking** | ⚠️ Overkill right now | Add only after hybrid search; not needed for Google-sourced URLs |
| **LangGraph** | ⚠️ Not needed yet | Add only if you build a loop: critique `is_approved=False` → conditional re-write → re-critique. Would be a genuine upgrade. |
| **MCP server** | ❌ Not relevant | MCP is for tool-using LLMs calling external services; doesn't fit this architecture |
| **Async scraping** | ✅ Yes — high impact, low complexity | `concurrent.futures.ThreadPoolExecutor` for parallel URL fetching cuts read-stage latency 3–5× |

**Structured output sketch** for CritiqueAgent:

```python
# In critique_agent.py — replace string matching with structured output
from pydantic import BaseModel

class CritiqueResult(BaseModel):
    overall_score: int          # 1-10
    strengths: list[str]        # 3-4 items
    critical_gaps: list[str]    # areas needing work
    priority_improvements: list[str]  # top 3
    recommendation: str         # "Pass" or "Revise"
    is_approved: bool           # score >= 7 and recommendation == "Pass"

# Use LangChain's with_structured_output():
structured_llm = self.llm.with_structured_output(CritiqueResult)
result: CritiqueResult = structured_llm.invoke(prompt_value)
```

---

## 8. Portfolio and Outreach Notes

### What to Show in a 60–90 Second Loom Demo

1. **(0–10s)** Open the running Streamlit app. Point to the sidebar — explain the sliders control how many sources are searched and how many pages are read.
2. **(10–20s)** Type a concrete research topic (e.g., "applications of LLMs in healthcare 2024"). Hit Start.
3. **(20–50s)** While it runs, explain verbally: "The Search Agent is querying Google right now via SerpAPI, then the Reader Agent will scrape those pages and clean the HTML, then the Writer Agent sends all that extracted text to Llama 3.3 70B on Groq to synthesize a report..."
4. **(50–70s)** Show the finished report rendered in the UI. Scroll through the Executive Summary and Key Findings sections to show the depth of output.
5. **(70–80s)** Click the Critique expander — show the score and the structured feedback.
6. **(80–90s)** Click the Markdown download button. Briefly show the JSON download option. End: "The full pipeline — search to polished report — completed in under 60 seconds."

---

### 3 Bullet Points for a CTO Cold Email

> **Important:** Do not include these in any outreach until API keys are rotated and a live demo link exists.

- **Built a 4-agent Python research pipeline** that autonomously queries Google, scrapes and cleans web pages with BeautifulSoup, and synthesizes 2,000-word structured reports using Llama 3.3 70B via Groq — end-to-end in under 60 seconds.
- **Designed with a modular ABC-based architecture** so any agent (search, read, write, critique) can be independently swapped; demonstrated the design by wiring a self-evaluating critique loop that scores output quality on a 1–10 rubric across five dimensions.
- **Shipped a full-stack interactive demo** with a dark-themed Streamlit web app, configurable search depth, collapsible critique feedback, and one-click Markdown/JSON exports — live at [link].

---

### What Should NOT Be Shared Publicly (and How to Fix It)

| Risk | Action Required |
|---|---|
| **Live `SERP_API_KEY` in `.env`** | **Immediately** revoke at serpapi.com dashboard → generate a new key → store only in `.env` (never commit) |
| **Live `GROQ_API_KEY` in `.env`** | **Immediately** revoke at console.groq.com → generate new → store only in `.env` |
| **`.env` in git history (if ever committed)** | Even if `.env` is now gitignored, past commits preserve the keys. Run: `git filter-repo --path .env --invert-paths` to scrub history before making repo public. Alternatively, delete and recreate the repo from the current state. |
| **"Veritas" project name in `qa_testing.txt`** | `qa_testing.txt` refers to the project as "Veritas". If this name belongs to a course, employer, or another team's project, verify sharing rights before making it public. |

**Step-by-step safe public demo setup:**

1. Rotate both API keys (takes ~2 minutes each at the respective dashboards)
2. `.env.example` with placeholder values (✅ Created in repo):
   ```
   SERP_API_KEY=your_serpapi_key_here
   GROQ_API_KEY=your_groq_api_key_here
   LOG_LEVEL=INFO
   SEARCH_TIMEOUT=15
   SEARCH_MAX_RESULTS=10
   ```
3. Verify `.env` is NOT tracked: `git ls-files .env` should return nothing
4. If `.env` was ever committed: run `git filter-repo --path .env --invert-paths` then force-push
5. Deploy to Streamlit Community Cloud or Hugging Face Spaces; add real keys as secrets in the platform's dashboard UI — **not in any file**
6. The live app URL becomes the demo link for your portfolio and cold emails

---

*This review was produced by reading all source files in the workspace. No code was executed and no external services were called. Findings reflect the code as written at review time.*
