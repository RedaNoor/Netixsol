import logging
import time
import uuid
from .db import save_pending, update_approval
from .graph import agent_graph
from .schemas import AgentResult, ClientRequest, ApprovalRequest

logger = logging.getLogger("agent.service")

def run_agent(request: ClientRequest, approval_base_url: str = "") -> AgentResult:
    request_id = str(uuid.uuid4())
    started = time.perf_counter()
    try:
        state = agent_graph.invoke({"request": request, "warnings": []})
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        approval_url = f"{approval_base_url.rstrip('/')}/approvals/{request_id}" if approval_base_url else f"/approvals/{request_id}"
        metrics = dict(state.get("metrics", {}))
        metrics["end_to_end_latency_ms"] = latency_ms
        metrics["tool_source"] = "SQLite service catalog + local company profile file"
        result = AgentResult(
            request_id=request_id,
            status="pending_approval",
            lead_score=state["lead_score"],
            lead_tier=state["lead_tier"],
            feasibility=state["feasibility"],
            proposal=state["proposal"],
            warnings=state.get("warnings", []),
            approval_url=approval_url,
            metrics=metrics,
        )
        save_pending(request_id, request.email, request.model_dump(mode="json"), result.model_dump(mode="json"))
        logger.info("agent run completed", extra={"request_id": request_id, "event": "run_complete", "latency_ms": latency_ms})
        return result
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.exception("agent run failed", extra={"request_id": request_id, "event": "run_failed", "latency_ms": latency_ms, "error": str(exc)})
        return AgentResult(
            request_id=request_id, status="failed", lead_score=0, lead_tier="low", feasibility="needs_discovery",
            warnings=["The request could not be completed safely.", f"{type(exc).__name__}: {exc}"],
            metrics={"end_to_end_latency_ms": latency_ms},
        )

def apply_approval(request_id: str, approval: ApprovalRequest) -> AgentResult | None:
    result = update_approval(request_id, approval.approve, approval.reviewer_notes)
    return AgentResult(**result) if result else None
