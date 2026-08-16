# Requirements & Defect Audit

## Capstone requirements

| Requirement | Status | Evidence |
|---|---|---|
| Real Web3/freelance business use case | PASS | Client onboarding/proposal workflow |
| Architecture diagram/design | PASS | `docs/architecture.md` |
| Framework rationale | PASS | `docs/architecture.md` and README |
| End-to-end agent | PASS | `app/graph.py`, `app/service.py` |
| External data/tool | PASS | company profile + SQLite service catalog |
| Human-in-the-loop | PASS | `/approvals` browser UI + approval API + SQLite persistence |
| Input validation | PASS | `app/schemas.py` |
| Bad input handling | PASS | HTTP 422 + tests |
| Tool timeout/error handling | PASS | `app/tools.py` + graph fallback |
| Model error handling | PASS | run is marked failed rather than falsely reporting success |
| Self-correction | PASS | `review -> revise -> review` |
| Evaluation 4–6 criteria | PASS | 6 criteria in `eval/run_eval.py` |
| 8 varied tests | PASS | `eval/test_cases.json` |
| 2 edge/adversarial tests | PASS | T7 and T8 |
| Failure pattern + concrete fix | PASS | feasibility gate in `app/graph.py` |
| FastAPI wrapper | PASS | `app/main.py` |
| Monitoring/logging | PASS | JSON logs + monitoring checklist |
| Token usage | PASS | OpenRouter/OpenAI usage metadata |
| Cost tracking | PASS | estimated cost from configured model rates |
| Executive report | UPDATE REQUIRED | Generate final report after real evaluation run |
| Presentation outline | PASS | `docs/slide_outline.md` |

## Reported defects

### 1. Stable Python version missing
**Previous status:** defect.

**Current status:** FIXED. `README.md` explicitly recommends Python 3.12.x and gives setup commands.

### 2. `requirements.txt` missing
**Previous status:** defect.

**Current status:** FIXED. Root `requirements.txt` is present and includes all runtime/test dependencies.

### 3. Fuzzy search returns the same typed name
**Status:** NOT APPLICABLE TO THIS CAPSTONE.

This codebase contains no fuzzy user-name search, user directory lookup, or name-resolution feature. It would be incorrect to claim that fuzzy search is supported. The README explicitly records this scope boundary.

### 4. “Network error in app” categorized as general instead of technical
**Status:** NOT APPLICABLE TO THIS CAPSTONE.

This project is a client-onboarding/proposal agent, not a support-ticket classifier. There is no `general`/`technical` ticket taxonomy in the code. If the intended capstone is actually a support-ticket triage agent, the use case and evaluation suite must be changed rather than adding an unrelated classifier to this project.

### 5. No human intervention for approval
**Previous status:** PARTIAL DEFECT.

The earlier implementation exposed only an API endpoint. The current version adds a real browser-based approval flow:
- `GET /approvals` lists pending proposals.
- `GET /approvals/{request_id}` displays the proposal and reviewer controls.
- Reviewer clicks Approve or Reject and can enter notes.
- Decision is persisted in SQLite.
- The API approval endpoint remains available for programmatic clients.

## Verification limitation

The repository can be statically checked and syntax-compiled without credentials. A live OpenRouter model call cannot be verified until the user sets `OPENROUTER_API_KEY` in `.env`. The evaluation script is deliberately configured to use the real OpenRouter model so the final CSV reflects actual runs rather than fabricated baseline values.
