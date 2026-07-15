# Agentic AI Job Search — Full Notes

Complete documentation for the **10-agent LangGraph job search system**, including architecture, agent roles, state schema, and usage guides.

## Resume Library (6 Candidates)

| File | Candidate | Target Role |
|------|-----------|-------------|
| `data/resumes/alex_chen_ml_engineer.txt` | Alex Chen | ML Engineer / AI Engineer |
| `data/resumes/priya_sharma_data_scientist.txt` | Priya Sharma | Data Scientist |
| `data/resumes/marcus_johnson_devops.txt` | Marcus Johnson | DevOps / Platform Engineer |
| `data/resumes/elena_rodriguez_nlp_researcher.txt` | Elena Rodriguez | NLP Research Scientist |
| `data/resumes/james_okafor_ai_engineer.txt` | James Okafor | LLM / AI Engineer |
| `data/resumes/sarah_kim_junior_engineer.txt` | Sarah Kim | Junior Software Engineer |

Add new `.txt` files to `data/resumes/` to include them in batch runs automatically.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Why LangGraph](#2-why-langgraph)
3. [Architecture](#3-architecture)
4. [The 10 Agents](#4-the-10-agents)
5. [LangGraph Workflow](#5-langgraph-workflow)
6. [State Schema](#6-state-schema)
7. [Project Structure](#7-project-structure)
8. [Setup & Installation](#8-setup--installation)
9. [Running the System](#9-running-the-system)
10. [Streamlit UI Guide](#10-streamlit-ui-guide)
11. [CLI Reference](#11-cli-reference)
12. [LLM Configuration](#12-llm-configuration)
13. [Extending the System](#13-extending-the-system)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Overview

This project is a **multi-agent AI job search assistant**. Ten specialized agents collaborate through a **LangGraph** state machine to automate:

- Resume parsing and profile extraction
- Job discovery and ranking
- Skills matching and gap analysis
- Salary and company research
- Application tracking and shortlisting
- Cover letter and resume optimization
- Interview preparation
- Final actionable report generation

Each agent is a **node** in a LangGraph `StateGraph`. Shared data flows through a single **GraphState** object that every node reads and updates.

---

## 2. Why LangGraph

| Feature | Benefit |
|---------|---------|
| **StateGraph** | Explicit shared state passed between agents |
| **Nodes & Edges** | Clear, visual pipeline definition |
| **Parallel branches** | Salary + Company research run concurrently |
| **Streaming** | Live UI updates as each agent completes |
| **Checkpointing** | Ready for persistence and human-in-the-loop |
| **Mermaid export** | Auto-generated workflow diagrams |

LangGraph replaces a simple `for agent in agents` loop with a **declarative graph** that is easier to extend, debug, and visualize.

---

## 3. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     LangGraph StateGraph                          │
│                                                                   │
│  START ──► Orchestrator ──► ProfileAnalyzer ──► JobSearcher      │
│                                    │                              │
│                                    ▼                              │
│                             SkillsMatcher                         │
│                              ╱         ╲                          │
│                             ╱           ╲   (parallel)            │
│                   SalaryAnalyst    CompanyResearcher               │
│                             ╲           ╱                          │
│                              ╲         ╱                          │
│                          ApplicationTracker                       │
│                                    │                              │
│                                    ▼                              │
│              CoverLetter ──► ResumeOptimizer ──► InterviewPrep    │
│                                    │                              │
│                                    ▼                              │
│                           ReportGenerator ──► END                 │
└──────────────────────────────────────────────────────────────────┘
```

### Layers

| Layer | Purpose |
|-------|---------|
| **UI** (`ui/app.py`) | Streamlit dashboard — run pipeline, view agents, results |
| **Graph** (`graph/`) | LangGraph workflow, nodes, state, report |
| **Agents** (`agents/`) | Individual agent logic (LLM + rules) |
| **Services** (`services/`) | LLM wrapper, job data sources |
| **Models** (`models/`) | Pydantic schemas for type safety |

---

## 4. The 10 Agents

### Agent 1: ProfileAnalyzer

- **Node ID:** `profile_analyzer`
- **Input:** Raw resume text from `user_profile.raw_resume`
- **Output:** Structured profile (name, skills, experience, target roles)
- **File:** `agents/profile_analyzer.py`

Parses unstructured resume text into a structured `UserProfile`. Uses LLM JSON extraction when an API key is set; falls back to rule-based parsing in demo mode.

### Agent 2: JobSearcher

- **Node ID:** `job_searcher`
- **Input:** Profile skills, target roles, search query
- **Output:** Ranked list of `JobListing` objects
- **File:** `agents/job_searcher.py`

Searches mock job listings (extensible to real APIs like LinkedIn, Indeed). Optionally re-ranks results with LLM based on profile fit.

### Agent 3: SkillsMatcher

- **Node ID:** `skills_matcher`
- **Input:** Profile skills + job requirements
- **Output:** `SkillMatchResult` per job (0–100% score)
- **File:** `agents/skills_matcher.py`

Compares candidate skills against each job's requirements. Identifies matched skills, gaps, and recommendations.

### Agent 4: SalaryAnalyst

- **Node ID:** `salary_analyst`
- **Input:** Top 5 matched jobs + salary expectations
- **Output:** `SalaryAnalysis` with market estimates and negotiation tips
- **File:** `agents/salary_analyst.py`
- **Runs in parallel with:** CompanyResearcher

### Agent 5: CompanyResearcher

- **Node ID:** `company_researcher`
- **Input:** Top matched companies
- **Output:** `CompanyProfile` (culture, pros/cons, interview process)
- **File:** `agents/company_researcher.py`
- **Runs in parallel with:** SalaryAnalyst

### Agent 6: ApplicationTracker

- **Node ID:** `application_tracker`
- **Input:** Skill matches (after parallel phase completes)
- **Output:** `JobApplication` records + shortlisted job IDs
- **File:** `agents/application_tracker.py`

Shortlists jobs with match score ≥ 65%. Tracks status: discovered → matched → shortlisted → applied.

### Agent 7: CoverLetterWriter

- **Node ID:** `cover_letter_writer`
- **Input:** Shortlisted jobs + profile + skill matches
- **Output:** Personalized `CoverLetter` per job (top 3)
- **File:** `agents/cover_letter_writer.py`

### Agent 8: ResumeOptimizer

- **Node ID:** `resume_optimizer`
- **Input:** Profile + target job descriptions
- **Output:** `ResumeOptimization` with ATS keywords and bullet rewrites
- **File:** `agents/resume_optimizer.py`

### Agent 9: InterviewPrep

- **Node ID:** `interview_prep`
- **Input:** Shortlisted jobs + company research
- **Output:** `InterviewPrep` with Q&A and tips
- **File:** `agents/interview_prep.py`

### Agent 10: Orchestrator + ReportGenerator

- **Orchestrator Node ID:** `orchestrator` — pipeline entry, logs start
- **Report Node ID:** `report_generator` — synthesizes final report
- **Files:** `graph/nodes.py`, `graph/report.py`, `graph/workflow.py`

The orchestrator is the LangGraph entry node. ReportGenerator is the final node that produces the downloadable report.

---

## 5. LangGraph Workflow

### Graph Definition

File: `graph/workflow.py`

```python
from langgraph.graph import END, START, StateGraph

builder = StateGraph(GraphState)

# Add nodes
builder.add_node("profile_analyzer", profile_analyzer_node)
# ... all 11 nodes

# Sequential flow
builder.add_edge(START, "orchestrator")
builder.add_edge("orchestrator", "profile_analyzer")
builder.add_edge("profile_analyzer", "job_searcher")
builder.add_edge("job_searcher", "skills_matcher")

# Parallel fan-out / fan-in
builder.add_edge("skills_matcher", "salary_analyst")
builder.add_edge("skills_matcher", "company_researcher")
builder.add_edge(["salary_analyst", "company_researcher"], "application_tracker")

# Continue sequentially
builder.add_edge("application_tracker", "cover_letter_writer")
# ... through report_generator
builder.add_edge("report_generator", END)

graph = builder.compile()
```

### Running the Graph

```python
from graph.workflow import run_pipeline, stream_pipeline
from models.schemas import UserProfile

# Blocking run
state = run_pipeline(
    profile=UserProfile(raw_resume="..."),
    search_query="ML Engineer Python",
)

# Streaming (for UI)
for event in stream_pipeline(profile=profile, search_query=query):
    for node_name, output in event.items():
        print(f"Completed: {node_name}")
```

### Node Wrapper Pattern

Each LangGraph node wraps an existing agent:

```python
def _make_node(agent_cls, agent_key):
    def node(state: GraphState) -> GraphState:
        agent = agent_cls(get_llm())
        js = to_job_search_state(state)
        js = agent.run(js)
        return from_job_search_state(js, current_agent=agent_key)
    return node
```

---

## 6. State Schema

### GraphState (LangGraph TypedDict)

File: `graph/state.py`

| Field | Type | Description |
|-------|------|-------------|
| `user_profile` | dict | Candidate profile |
| `search_query` | str | Job search keywords |
| `job_listings` | list[dict] | Discovered jobs |
| `skill_matches` | list[dict] | Match scores per job |
| `salary_analyses` | list[dict] | Compensation analysis |
| `company_profiles` | list[dict] | Company research |
| `cover_letters` | list[dict] | Generated letters |
| `resume_optimizations` | list[dict] | ATS optimizations |
| `interview_preps` | list[dict] | Interview guides |
| `applications` | list[dict] | Application tracker |
| `agent_messages` | list[dict] | Activity log |
| `shortlisted_job_ids` | list[str] | Jobs ≥ 65% match |
| `final_report` | str | Final synthesized report |
| `current_agent` | str | Last completed node |
| `pipeline_status` | str | pending / running / complete |

### JobSearchState (Pydantic)

File: `models/schemas.py` — strongly typed version used inside agents. Converted to/from `GraphState` via `to_job_search_state()` and `from_job_search_state()`.

---

## 7. Project Structure

```
Agentic AI Project 2/
├── agents/                    # Agent implementations (10 agents)
│   ├── base.py
│   ├── profile_analyzer.py    # Agent 1
│   ├── job_searcher.py        # Agent 2
│   ├── skills_matcher.py      # Agent 3
│   ├── salary_analyst.py      # Agent 4
│   ├── company_researcher.py  # Agent 5
│   ├── application_tracker.py # Agent 6
│   ├── cover_letter_writer.py # Agent 7
│   ├── resume_optimizer.py    # Agent 8
│   ├── interview_prep.py      # Agent 9
│   └── orchestrator.py        # Legacy orchestrator (delegates to LangGraph)
├── graph/                     # LangGraph workflow
│   ├── state.py               # GraphState + converters
│   ├── nodes.py               # Node functions
│   ├── workflow.py            # Graph build & compile
│   └── report.py              # Report generation
├── ui/
│   └── app.py                 # Streamlit dashboard
├── docs/
│   └── NOTES.md               # This file
├── models/
│   └── schemas.py             # Pydantic models
├── services/
│   ├── llm_service.py         # OpenAI wrapper
│   └── job_sources.py         # Job listing data
├── data/
│   └── sample_resume.txt
├── output/                    # Generated reports
├── config.py
├── main.py                    # CLI
├── requirements.txt
└── .env.example
```

---

## 8. Setup & Installation

### Prerequisites

- Python 3.10+
- pip

### Install

```bash
cd "Agentic AI Project 2"
pip install -r requirements.txt
```

### Environment

```bash
copy .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=
```

Leave `OPENAI_API_KEY` empty to run in **demo mode** with rule-based fallbacks.

---

## 9. Running the System

### Option A: End-to-End Batch (All 6 Resumes)

```bash
# Process ALL resumes in data/resumes/ through full pipeline
python main.py demo-batch

# Or with options
python main.py batch --query "AI Engineer remote"
python main.py batch --ids alex_chen_ml_engineer,priya_sharma_data_scientist
```

Output structure:
```
output/{run_id}/
├── comparison_report.txt      # Cross-candidate comparison
├── batch_results.json         # Full batch data
├── INDEX.txt                  # Quick index
├── alex_chen_ml_engineer/
│   ├── final_report.txt
│   ├── full_results.json
│   ├── profile.json
│   ├── original_resume.txt
│   ├── cover_letter_*.txt
│   ├── optimized_resume_*.txt
│   └── interview_prep_*.json
├── priya_sharma_data_scientist/
└── ... (one folder per candidate)
```

### Option B: Streamlit UI (Recommended)

```bash
streamlit run ui/app.py
```

UI tabs:
- **Batch Run** — process all 6 resumes or single resume with live agent streaming
- **Candidates** — view all resume profiles
- **Results** — comparison report, per-candidate matches, cover letters, tailored resumes
- **Upload** — run pipeline on custom resume text/file
- **Agents** — LangGraph workflow diagram
- **Notes** — this documentation

### Option C: CLI Single Resume

```bash
# Demo
python main.py demo

# Custom query
python main.py run --query "AI Engineer remote"

# Specific resume
python main.py run --resume data/resumes/james_okafor_ai_engineer.txt

# List resume library
python main.py resumes

# List agents
python main.py agents

# Launch UI
python main.py ui
```

---

## 10. Streamlit UI Guide

### Tabs

| Tab | Purpose |
|-----|---------|
| **Run Pipeline** | Upload resume, set query, run LangGraph with live streaming |
| **Agents** | View all 10 agents, Mermaid workflow diagram, completion status |
| **Results** | Jobs, matches, salary, companies, cover letters, interview prep, report |
| **Notes** | Full documentation (this file) rendered in-app |

### Sidebar

- API key status (Live LLM vs Demo mode)
- Agent checklist with completion markers

### Live Streaming

When "Stream agent updates" is checked, the UI calls `stream_pipeline()` and updates progress as each LangGraph node completes.

### Downloads

From the Results → Report tab:
- Download `.txt` report
- Download full `.json` state

---

## 11. CLI Reference

```
Usage: python main.py [COMMAND]

Commands:
  run     Run the LangGraph job search pipeline
  demo    Quick demo with sample resume
  agents  List all 10 agents
  ui      Launch Streamlit dashboard

Options for `run`:
  -q, --query TEXT     Job search query
  -r, --resume PATH    Path to resume file
  -o, --output PATH    Output directory (default: output/)
```

---

## 12. LLM Configuration

### OpenAI (default)

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### Azure OpenAI / compatible APIs

```env
OPENAI_API_KEY=your-azure-key
OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/v1/
OPENAI_MODEL=gpt-4o-mini
```

### Demo Mode

Without an API key:
- Profile parsing uses rule-based extraction
- Skill matching uses heuristic scoring
- Cover letters use template text
- All pipeline steps still execute end-to-end

---

## 13. Extending the System

### Add a New Agent

1. Create `agents/my_agent.py` extending `BaseAgent`
2. Add node in `graph/nodes.py`:
   ```python
   my_agent_node = _make_node(MyAgent, "my_agent")
   ```
3. Register in `graph/workflow.py`:
   ```python
   builder.add_node("my_agent", my_agent_node)
   builder.add_edge("interview_prep", "my_agent")
   builder.add_edge("my_agent", "report_generator")
   ```
4. Add metadata to `NODE_REGISTRY` in `graph/nodes.py`
5. Update UI icons in `ui/app.py`

### Connect Real Job APIs

Edit `services/job_sources.py`:
- Replace `MOCK_JOBS` with API calls (LinkedIn, Indeed, Adzuna, etc.)
- Keep the `JobListing` return type

### Add Human-in-the-Loop

LangGraph supports interrupt nodes:

```python
from langgraph.checkpoint.memory import MemorySaver

graph = builder.compile(checkpointer=MemorySaver(), interrupt_before=["application_tracker"])
```

Pause before shortlisting to let the user approve jobs manually.

### Add Conditional Routing

Route low-match jobs to a "Upskilling Advisor" agent:

```python
def route_after_match(state):
    avg = sum(m["match_score"] for m in state["skill_matches"]) / len(state["skill_matches"])
    return "upskilling_advisor" if avg < 50 else "salary_analyst"

builder.add_conditional_edges("skills_matcher", route_after_match)
```

---

## 14. Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: langgraph` | Run `pip install -r requirements.txt` |
| Unicode error on Windows CLI | Use Streamlit UI or set `PYTHONIOENCODING=utf-8` |
| Cover letters show JSON | Ensure demo fallback order in `llm_service.py` |
| Low match scores | Add more skills to resume or set `OPENAI_API_KEY` |
| Streamlit won't start | Run from project root: `streamlit run ui/app.py` |
| Parallel node errors | Ensure LangGraph >= 0.2 for fan-in edge syntax |

---

## Quick Reference Card

```
Pipeline:  Resume → Profile → Search → Match → [Salary + Company] → Track → Cover Letter → Resume → Interview → Report

Run UI:    streamlit run ui/app.py
Run CLI:   python main.py demo
Graph:     graph/workflow.py
Agents:    agents/*.py
State:     graph/state.py + models/schemas.py
Notes:     docs/NOTES.md
```

---

*Built with LangGraph, OpenAI, Pydantic, and Streamlit.*
