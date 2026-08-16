# Architecture

```text
Client / Swagger UI
        |
        v
FastAPI + Pydantic validation
        |
        v
+------------------------- LangGraph -------------------------+
|                                                             |
|  enrich -> qualify -> draft -> safety/quality review        |
|     |          |         |              |                    |
|     |          |         |              +-> revise ----------+
|     |          |         |                                   |
| company     rule-based  OpenRouter                         |
| profile     feasibility  structured JSON                   |
| file        + lead score                                  |
| SQLite service catalog                                      |
+-------------------------------------------------------------+
        |
        v
SQLite: pending_approval
        |
        v
Human Approval Web Page / API
        |
   +----+----+
   |         |
Approve    Reject
```

## Framework choice
LangGraph is used because this is a control-heavy, stateful workflow with deterministic enrichment, qualification, model generation, review, conditional revision and a human gate. OpenRouter is used as the model gateway because its API is OpenAI-compatible, allowing the application to use the standard OpenAI Python client while selecting a routed model. FastAPI remains the transport and validation layer, keeping HTTP concerns separate from graph orchestration.
