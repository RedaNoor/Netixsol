# Web3Geeks Capstone — Production-Ready Client Onboarding & Proposal Agent

A LangGraph + OpenRouter + FastAPI capstone implementing validation, external/local data sources, lead qualification, structured proposal generation, self-correction, human approval, evaluation and monitoring.

## Stable Python version

**Recommended: Python 3.12.x (use 3.12.10 or another installed 3.12 maintenance release).** Python 3.12 is a mature compatibility target for this project. Python 3.14 is the latest feature series, but 3.12 is deliberately pinned as the capstone's stable target to reduce dependency compatibility surprises.

Check your version:

```bash
python --version
```

Expected:

```text
Python 3.12.x
```

## 1. OpenRouter setup

This version uses **OpenRouter instead of mock mode**. OpenRouter exposes an OpenAI-compatible API, so the project uses the OpenAI Python client with `base_url=https://openrouter.ai/api/v1`. The default model is `openai/gpt-4.1-mini`.

Create a `.env` file from `.env.example`:

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openai/gpt-4.1-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_SITE_URL=http://localhost:8000
OPENROUTER_APP_NAME=Web3Geeks Capstone Agent
```

**Never commit `.env`.** `.gitignore` already excludes it.

## 2. Local setup

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and insert your OpenRouter key.

## 3. Run the API

```bash
uvicorn app.main:app --reload
```

Open Swagger:

```text
http://127.0.0.1:8000/docs
```

Health:

```text
GET /health
```

Run an agent:

```text
POST /agent/run
```

Then open the returned `approval_url`, or visit:

```text
http://127.0.0.1:8000/approvals
```

This is the **actual human-in-the-loop checkpoint**. A reviewer opens the pending proposal, reads the requirements and generated scope, enters notes, then clicks **Approve Proposal** or **Reject Proposal**. The status is persisted in SQLite. The JSON approval endpoint is also available at `POST /agent/{request_id}/approval`.

## 4. Example request

```json
{
  "client_name": "Aisha Khan",
  "email": "aisha@example.com",
  "company": "FinNova",
  "project_type": "ai_agent",
  "requirements": "Build an internal support triage agent that classifies tickets, retrieves policy context, and drafts responses for staff review.",
  "budget_usd": 12000,
  "timeline_weeks": 8
}
```

## 5. Data sources/tools

The agent uses two local external-to-the-model data sources:

- `data/company_profile.md` — company policies and services.
- SQLite `data/capstone.db` — service prices, minimum timelines and descriptions.

Tool failures are caught and converted into conservative fallback state with a warning.

## 6. Failure handling

1. **Bad input:** Pydantic returns HTTP 422.
2. **Prompt injection:** obvious instruction-bypass markers are rejected before model execution.
3. **Tool timeout/error:** safe fallback context is used and a warning is recorded.
4. **Model error/refusal:** the request is returned as failed rather than silently pretending a successful model run occurred.
5. **Commercial mismatch:** a feasibility gate marks the lead `needs_discovery`; the proposal must explicitly surface the constraint.

## 7. Evaluation

Run:

```bash
python eval/run_eval.py
```

This sends all 8 cases through the **real OpenRouter model** and writes:

```text
eval/evaluation_results.csv
```

Criteria are scored 1–5:

- task success
- factual/commercial consistency
- proposal quality
- safety
- latency
- token efficiency

The cases include six normal requests, one low-budget/timeline edge case, and one prompt-injection adversarial case.

Do not submit fabricated evaluation numbers. Run the evaluator with your configured model and include the generated CSV.

## 8. Tests

```bash
pytest -q
```

The tests intentionally do not call OpenRouter. They verify API routing and input-validation behavior without spending API credits.

## 9. Logs

JSON logs are written to:

```text
logs/agent.log
```

The model call logs provider/model, latency, prompt tokens, completion tokens and estimated cost.

## 10. Architecture and presentation

See:

- `docs/architecture.md`
- `docs/monitoring_checklist.md`
- `docs/slide_outline.md`

