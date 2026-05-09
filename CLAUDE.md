# Control Room — CLAUDE.md

## 1. Project Overview

Control Room is a lightweight, self-hostable LLM evaluation and canary testing platform. It is a developer tool that allows engineers to detect regressions when swapping LLM models or updating prompts — before those changes hit production.

The core use case: a developer has a working LLM pipeline (e.g. GPT-4o). They want to swap to Gemini 1.5 Pro. Control Room lets them run their golden dataset against both models, scores outputs using an LLM-as-judge, and shows exactly where quality regressed and where it improved.

It is NOT a general observability tool. It is NOT a tracing tool. It is specifically focused on regression + canary testing for LLM pipeline changes.

Positioning: think LangSmith, but lightweight, self-hostable, provider-agnostic, and open source.

---

## 2. Architecture

Control Room has three layers that must remain cleanly separated:

```
[ Python SDK ]  →  [ FastAPI Backend ]  →  [ PostgreSQL ]
                                                 ↑
                                        [ React + Vite UI ]
```

- **SDK**: The user installs this via pip. They define datasets, run evals, and results are sent to the backend automatically.
- **Backend**: FastAPI. Receives eval results from the SDK, stores them in PostgreSQL, exposes REST API endpoints for the frontend.
- **Frontend**: React + Vite SPA. Displays eval run results, pass/fail per test case, regression comparisons over time.
- **Database**: PostgreSQL. Stores datasets, eval runs, individual test case results, judge scores.

**Critical rule**: The SDK must work independently of the UI. A developer should be able to run evals from the terminal with no UI running. Results get stored and the UI just reads from the DB.

---

## 3. Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| SDK | Python package (pip installable) | Users are Python developers |
| Backend | FastAPI | Fast, async, clean REST API |
| Database | PostgreSQL | Relational, handles eval run history well |
| Frontend | React + Vite | SPA pattern, no SSR needed for a dashboard |
| Infra | Docker (later, not v0.1) | Self-hosting requirement |

**Provider agnostic**: The SDK must work with OpenAI, Anthropic, Gemini, and local models. Never hardcode a provider. Users pass in their own LLM call function.

---

## 4. Folder Structure

```
control-room/
├── sdk/
│   ├── controlroom/
│   │   ├── __init__.py
│   │   ├── dataset.py       # Dataset and TestCase definitions
│   │   ├── models.py        # Pydantic models (EvalResult, TestCaseResult)
│   │   ├── runner.py        # Runs test cases against user's LLM
│   │   ├── scorer.py        # LLM-as-judge scoring logic
│   │   └── client.py        # Sends results to backend API
│   ├── pyproject.toml
│   └── README.md
├── backend/
│   ├── main.py
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # DB connection
│   ├── routes/
│   │   ├── runs.py          # Eval run endpoints
│   │   └── results.py       # Test case result endpoints
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── api/             # API calls to backend
│   └── vite.config.js
└── docs/
```

---

## 5. V0.1 Scope — STRICT BOUNDARY

V0.1 does exactly this and nothing more:

1. User defines a **Dataset** — a list of input/expected output pairs
2. User runs the dataset against **their own LLM function** via the SDK
3. Each output is scored by an **LLM-as-judge** (pass/fail + confidence score)
4. Results are sent to the **FastAPI backend** and stored in **PostgreSQL**
5. Results are visible in the **React UI** as a table: test case, input preview, expected, actual, score, pass/fail

**What is explicitly OUT of scope for v0.1:**
- User authentication
- Multiple projects or workspaces
- Canary comparison UI (Model A vs Model B diff) — this is v0.2
- Judge calibration pipeline — this is v0.3
- Docker / self-hosting setup
- PyPI publishing
- Streaming results in real time

Do not add features beyond this list without being explicitly told to.

---

## 6. SDK Design — How It Should Feel to the User

The SDK API must be simple. A user should be able to run their first eval in under 10 lines of code:

```python
from controlroom import Dataset, run_eval

dataset = Dataset([
    {"input": "What is the capital of France?", "expected": "Paris"},
    {"input": "What is 2 + 2?", "expected": "4"},
])

def my_llm(input: str) -> str:
    # user's own LLM call here
    return call_openai(input)

results = run_eval(dataset=dataset, llm=my_llm, run_name="gpt4o-baseline")
```

This is the north star for SDK design. Every design decision should be evaluated against this simplicity standard.

---

## 7. Scoring — LLM-as-Judge

The scorer in `scorer.py` uses an LLM to judge whether the actual output matches the expected output semantically (not exact match).

**Judge prompt structure:**
- System: You are an expert evaluator. Given an input, expected output, and actual output, determine if the actual output is correct.
- Return: JSON with `pass` (boolean), `confidence` (0.0-1.0), `reasoning` (string)

**Default judge model**: Claude claude-sonnet-4-20250514 via Anthropic API (configurable by user).

**Key rule**: The judge must return structured JSON always. Use instructor or manual JSON parsing with retry logic. Never let a malformed judge response crash an eval run.

---

## 8. Database Schema — Core Tables

```sql
-- An eval run (one execution of a dataset against an LLM)
eval_runs (
    id UUID PRIMARY KEY,
    run_name VARCHAR,
    model_name VARCHAR,
    created_at TIMESTAMP,
    total_cases INT,
    passed INT,
    failed INT
)

-- Individual test case results
test_results (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES eval_runs(id),
    input TEXT,
    expected TEXT,
    actual TEXT,
    passed BOOLEAN,
    confidence FLOAT,
    reasoning TEXT,
    created_at TIMESTAMP
)
```

---

## 9. Coding Conventions

**Python (SDK + Backend):**
- Type hints everywhere, no exceptions
- Pydantic models for all data structures
- No global state
- Functions over classes where possible
- Descriptive variable names, no abbreviations

**React (Frontend):**
- Functional components only, no class components
- Custom hooks for all API calls
- No inline styles — use CSS modules or Tailwind
- Keep components small and single-purpose

**General:**
- Every function needs a docstring
- No hardcoded API keys or URLs anywhere — use environment variables
- `.env.example` file must be kept updated

---

## 10. What Claude Should NOT Do

- Do not add features not listed in V0.1 scope
- Do not implement authentication in v0.1
- Do not hardcode any LLM provider — always keep it user-configurable
- Do not use LangChain or LangGraph in this project — keep dependencies minimal
- Do not make the SDK dependent on the backend being running
- Do not over-engineer — prefer simple, readable code over clever code
- Do not create files outside the defined folder structure without discussion

---

## 11. Current Build Status (as of v0.1)
- SDK: Complete and tested. All five modules done.
- Backend: Complete. Three endpoints working, connected to Supabase.
- Frontend: Not started. Next step.
- Full stack test: Passing. eval runs stored and retrievable.
