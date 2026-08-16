from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from .schemas import ClientRequest, ProposalDraft
from .tools import load_company_profile, lookup_service, ToolError
from .llm import create_proposal

class AgentState(TypedDict, total=False):
    request: ClientRequest
    company_profile: str
    service: dict
    lead_score: int
    lead_tier: str
    feasibility: str
    proposal: ProposalDraft
    warnings: list[str]
    metrics: dict
    review_ok: bool
    revision_count: int

def enrich_node(state: AgentState):
    warnings = list(state.get("warnings", []))
    try:
        return {"company_profile": load_company_profile(), "service": lookup_service(state["request"].project_type), "warnings": warnings}
    except ToolError as exc:
        warnings.append(f"External data tool failure: {exc}. Safe fallback used; human review remains mandatory.")
        return {
            "company_profile": "Human approval required. Never guarantee outcomes.",
            "service": {"base_price": 3500, "min_weeks": 3, "description": "Custom discovery and delivery"},
            "warnings": warnings,
        }

def qualify_node(state: AgentState):
    req, service = state["request"], state["service"]
    budget_ok = req.budget_usd >= service["base_price"]
    timeline_ok = req.timeline_weeks >= service["min_weeks"]
    score = 35 + (30 if budget_ok else 5) + (20 if timeline_ok else 5) + (15 if len(req.requirements) >= 80 else 8)
    score = min(100, score)
    tier = "high" if score >= 80 else "medium" if score >= 60 else "low"
    feasibility = "feasible" if budget_ok and timeline_ok else "needs_discovery"
    return {"lead_score": score, "lead_tier": tier, "feasibility": feasibility}

def draft_node(state: AgentState):
    proposal, metrics, warnings = create_proposal(state["request"], state["service"], state["company_profile"])
    return {"proposal": proposal, "metrics": metrics, "warnings": list(state.get("warnings", [])) + warnings, "revision_count": state.get("revision_count", 0)}

def review_node(state: AgentState):
    p = state["proposal"]
    service = state["service"]
    text = p.model_dump_json().lower()
    forbidden = ("guaranteed profit", "100% secure", "guaranteed growth", "guaranteed outcome")
    complete = all([p.executive_summary, len(p.proposed_scope) >= 3, p.assumptions, p.exclusions, p.risks, len(p.next_steps) >= 2])
    commercial_consistency = p.estimated_price_usd >= service["base_price"] and p.estimated_timeline_weeks >= service["min_weeks"]
    safe = not any(term in text for term in forbidden)
    return {"review_ok": complete and commercial_consistency and safe}

def revise_node(state: AgentState):
    p = state["proposal"]
    data = p.model_dump()
    if state["feasibility"] == "needs_discovery":
        data["risks"] = list(dict.fromkeys(data["risks"] + ["Requested budget or timeline is below the service minimum; discovery/phasing is required."]))
        data["next_steps"] = list(dict.fromkeys(data["next_steps"] + ["Review feasibility with a human project manager"]))
    data["assumptions"] = data["assumptions"] or ["Requirements will be confirmed during discovery."]
    data["exclusions"] = data["exclusions"] or ["No guaranteed commercial, legal, or security outcomes."]
    return {"proposal": ProposalDraft(**data), "revision_count": state.get("revision_count", 0) + 1}

def route_after_review(state: AgentState):
    if state.get("review_ok") or state.get("revision_count", 0) >= 1:
        return "finish"
    return "revise"

def finish_node(state: AgentState):
    return {}

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("enrich", enrich_node)
    graph.add_node("qualify", qualify_node)
    graph.add_node("draft", draft_node)
    graph.add_node("review", review_node)
    graph.add_node("revise", revise_node)
    graph.add_node("finish", finish_node)
    graph.add_edge(START, "enrich")
    graph.add_edge("enrich", "qualify")
    graph.add_edge("qualify", "draft")
    graph.add_edge("draft", "review")
    graph.add_conditional_edges("review", route_after_review, {"finish": "finish", "revise": "revise"})
    graph.add_edge("revise", "review")
    graph.add_edge("finish", END)
    return graph.compile()

agent_graph = build_graph()
