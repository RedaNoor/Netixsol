# 5-7 Minute Presentation

1. **Business problem — 45 sec**
   - Standardize inconsistent client inquiries.
   - Reduce manual qualification/proposal effort.
   - Keep commercial approval human-controlled.

2. **Architecture — 60 sec**
   - FastAPI -> LangGraph -> local company profile + SQLite -> OpenRouter -> review -> human approval.

3. **Why LangGraph/OpenRouter — 45 sec**
   - Explicit state and routing for workflow control.
   - OpenRouter gives a model gateway while keeping the app provider-independent at the client layer.

4. **Reliability & safety — 60 sec**
   - Pydantic validation.
   - Prompt-injection rejection.
   - Tool timeout fallback.
   - Structured model output.
   - Quality/safety review and revision.
   - Human approval UI and API.

5. **Evaluation — 60 sec**
   - 8 cases: 6 normal, 1 feasibility edge, 1 adversarial.
   - 6 criteria: success, accuracy, quality, safety, latency, efficiency.
   - Discuss failures from the actual run rather than invented numbers.

6. **API & monitoring — 45 sec**
   - Swagger endpoint.
   - Approval page.
   - JSON logs with latency, usage, cost estimate and errors.

7. **Limitations/next steps — 45 sec**
   - SQLite -> managed DB.
   - Add authentication/RBAC.
   - Connect CRM/email.
   - Expand evaluation set.
