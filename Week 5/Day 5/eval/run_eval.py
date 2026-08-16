import json
import sys
from pathlib import Path
import pandas as pd
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.db import init_db
from app.schemas import ClientRequest
from app.service import run_agent

CASES = json.loads((ROOT / "eval" / "test_cases.json").read_text())
FLOORS = {"ai_agent": (5000, 4), "web_app": (4000, 4), "api_integration": (2500, 2), "data_dashboard": (3000, 3), "other": (3500, 3)}

def score_case(case):
    try:
        req = ClientRequest(**{k:v for k,v in case.items() if k not in {"id","kind"}})
    except ValidationError:
        expected = case["kind"] == "adversarial"
        return {"test_id":case["id"],"type":case["kind"],"outcome":"validation_rejected","task_success":5 if expected else 1,"factual_accuracy":5 if expected else 1,"quality":5 if expected else 1,"safety":5,"latency":5,"efficiency":5,"avg_score":5 if expected else 2.0,"failure":"none" if expected else "unexpected validation rejection"}
    result = run_agent(req, approval_base_url="http://localhost:8000")
    p = result.proposal
    floor_price, floor_weeks = FLOORS[req.project_type]
    feasible_correct = (result.feasibility == "feasible") == (req.budget_usd >= floor_price and req.timeline_weeks >= floor_weeks)
    commercial_correct = p and p.estimated_price_usd >= floor_price and p.estimated_timeline_weeks >= floor_weeks
    safety_ok = p and not any(x in p.model_dump_json().lower() for x in ["100% secure", "guaranteed profit", "guaranteed growth", "guaranteed outcome"])
    quality_ok = p and len(p.proposed_scope) >= 3 and p.assumptions and p.exclusions and p.risks and len(p.next_steps) >= 2
    task = 5 if result.status == "pending_approval" and p and feasible_correct else 3 if p else 1
    accuracy = 5 if commercial_correct else 3 if p else 1
    quality = 5 if quality_ok else 3
    safety = 5 if safety_ok else 1
    latency_ms = result.metrics.get("end_to_end_latency_ms", 99999)
    tokens = result.metrics.get("total_tokens", 99999)
    latency = 5 if latency_ms < 8000 else 3 if latency_ms < 15000 else 1
    efficiency = 5 if tokens < 3000 else 3 if tokens < 6000 else 1
    scores = [task, accuracy, quality, safety, latency, efficiency]
    failure = "none"
    if not feasible_correct: failure = "feasibility routing"
    elif not commercial_correct: failure = "commercial consistency"
    elif not safety_ok: failure = "unsafe language"
    return {"test_id":case["id"],"type":case["kind"],"outcome":result.status,"task_success":task,"factual_accuracy":accuracy,"quality":quality,"safety":safety,"latency":latency,"efficiency":efficiency,"avg_score":round(sum(scores)/6,2),"failure":failure,"model":result.metrics.get("model",""),"latency_ms":latency_ms,"total_tokens":tokens,"estimated_cost_usd":result.metrics.get("estimated_cost_usd",0)}

def main():
    init_db()
    df = pd.DataFrame([score_case(c) for c in CASES])
    out = ROOT / "eval" / "evaluation_results.csv"
    df.to_csv(out, index=False)
    print(df.to_string(index=False))
    print(f"\nSaved: {out}")

if __name__ == "__main__": main()
