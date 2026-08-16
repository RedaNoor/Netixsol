import html
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from .db import init_db, get_proposal, list_pending
from .logging_config import configure_logging
from .schemas import ClientRequest, AgentResult, ApprovalRequest
from .service import run_agent, apply_approval

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()
    yield

app = FastAPI(
    title="Web3Geeks Client Onboarding & Proposal Agent",
    version="2.0.0",
    description="LangGraph + OpenRouter + FastAPI capstone with validation, evaluation, logging and a real human approval UI.",
    lifespan=lifespan,
)

@app.get("/health")
def health():
    return {"status": "ok", "model_provider": "OpenRouter"}

@app.post("/agent/run", response_model=AgentResult)
def agent_run(payload: ClientRequest):
    return run_agent(payload, approval_base_url="http://127.0.0.1:8000")

@app.get("/approvals", response_class=HTMLResponse)
def approvals():
    rows = list_pending()
    items = "".join(
        f'<li><a href="/approvals/{html.escape(r["request_id"])}">{html.escape(r["request_id"])}</a> — {html.escape(json.loads(r["request_json"])["company"])}</li>'
        for r in rows
    ) or "<li>No pending approvals.</li>"
    return HTMLResponse(f"""<html><head><title>Pending Approvals</title></head><body style='font-family:Arial;max-width:900px;margin:40px auto'><h1>Pending Human Approvals</h1><p>Open a proposal, review it, then explicitly approve or reject it.</p><ul>{items}</ul></body></html>""")

@app.get("/approvals/{request_id}", response_class=HTMLResponse)
def approval_page(request_id: str):
    row = get_proposal(request_id)
    if not row:
        raise HTTPException(status_code=404, detail="request_id not found")
    request_data = json.loads(row["request_json"])
    result = json.loads(row["result_json"])
    proposal = result.get("proposal") or {}
    def bullets(values):
        return "".join(f"<li>{html.escape(str(v))}</li>" for v in values)
    disabled = "disabled" if row["status"] != "pending_approval" else ""
    return HTMLResponse(f"""
    <html><head><title>Human Approval</title></head>
    <body style='font-family:Arial;max-width:900px;margin:40px auto;line-height:1.5'>
    <h1>Human Approval Checkpoint</h1>
    <p><b>Status:</b> {html.escape(row['status'])}</p>
    <h2>Client</h2><p>{html.escape(request_data['client_name'])} — {html.escape(request_data['company'])} — {html.escape(request_data['email'])}</p>
    <p><b>Project:</b> {html.escape(request_data['project_type'])}<br><b>Budget:</b> ${request_data['budget_usd']:,}<br><b>Timeline:</b> {request_data['timeline_weeks']} weeks</p>
    <h2>Requirements</h2><p>{html.escape(request_data['requirements'])}</p>
    <h2>Proposal</h2><p>{html.escape(proposal.get('executive_summary',''))}</p>
    <h3>Scope</h3><ul>{bullets(proposal.get('proposed_scope',[]))}</ul>
    <h3>Assumptions</h3><ul>{bullets(proposal.get('assumptions',[]))}</ul>
    <h3>Exclusions</h3><ul>{bullets(proposal.get('exclusions',[]))}</ul>
    <h3>Risks</h3><ul>{bullets(proposal.get('risks',[]))}</ul>
    <p><b>Estimated price:</b> ${proposal.get('estimated_price_usd',0):,}<br><b>Estimated timeline:</b> {proposal.get('estimated_timeline_weeks',0)} weeks</p>
    <h2>Decision</h2>
    <form method='post' action='/approvals/{html.escape(request_id)}'>
      <textarea name='reviewer_notes' rows='5' cols='80' placeholder='Reviewer notes...' {disabled}></textarea><br><br>
      <button name='approve' value='true' {disabled}>Approve Proposal</button>
      <button name='approve' value='false' {disabled}>Reject Proposal</button>
    </form>
    </body></html>""")

@app.post("/approvals/{request_id}", response_class=HTMLResponse)
def submit_approval(request_id: str, approve: bool, reviewer_notes: str = ""):
    result = apply_approval(request_id, ApprovalRequest(approve=approve, reviewer_notes=reviewer_notes))
    if result is None:
        raise HTTPException(status_code=404, detail="request_id not found")
    return HTMLResponse(f"""<html><body style='font-family:Arial;max-width:700px;margin:40px auto'><h1>Decision Recorded</h1><p>Status: <b>{html.escape(result.status)}</b></p><p>{html.escape(result.reviewer_notes or '')}</p><a href='/approvals'>Back to pending approvals</a></body></html>""")

@app.post("/agent/{request_id}/approval", response_model=AgentResult)
def approval_api(request_id: str, payload: ApprovalRequest):
    result = apply_approval(request_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="request_id not found")
    return result
