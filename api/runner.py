"""
Return Detective — Runner Service (Cloud Run rd-runner)
Provides execution endpoints:
  - POST /run-candidates (as_of): Scans daily_rates, triggers Chief Inspector for all candidates
  - POST /simulate-days {days: 7}: Appends +7 days of post-intervention operations & triggers Auditor
  - POST /audit-verifying: Runs Auditor over cases in 'verifying' and closes resolved cases
  - POST /reset: Resets demo state
"""

import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
import httpx
from dotenv import load_dotenv

from sql.find_candidates import find_case_candidates
from agents.return_detective.agent import process_candidate, check_and_create_refund_abuse_case
from agents.return_detective.sub_agents.auditor import audit_case
from data.generate_after import generate_7_days_after

load_dotenv()

app = FastAPI(
    title="Return Detective Runner Service",
    description="Automation and batch agent runner service for candidate processing and post-intervention audits",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RD_API_URL = os.getenv("RD_API_URL", "http://localhost:8000")

@app.get("/")
def runner_health():
    return {"service": "rd-runner", "status": "active"}

@app.post("/run-candidates")
def run_candidates(as_of: Optional[str] = "2026-10-18"):
    """
    Executes Chief Inspector across all candidate cases identified in daily_rates,
    plus checks for coordinated photo reuse refund abuse.
    """
    print(f"🚀 rd-runner: Scanning and executing candidates for {as_of}...")
    df = find_case_candidates(as_of)
    processed_cases = []
    
    for _, row in df.iterrows():
        cand = row.to_dict()
        case_file = process_candidate(cand)
        processed_cases.append({
            "case_id": case_file.case_id,
            "title": case_file.title,
            "status": case_file.status,
            "root_cause": case_file.finding.get("root_cause") if case_file.finding else None,
            "rupee_lost": case_file.rupee_lost
        })
        
    # Check for Scenario 5 refund abuse
    abuse_case = check_and_create_refund_abuse_case()
    if abuse_case:
        processed_cases.append({
            "case_id": abuse_case.case_id,
            "title": abuse_case.title,
            "status": abuse_case.status,
            "root_cause": "refund_abuse",
            "rupee_lost": abuse_case.rupee_lost
        })

    return {
        "status": "completed",
        "as_of": as_of,
        "cases_processed_count": len(processed_cases),
        "cases": processed_cases
    }

@app.post("/simulate-days")
def simulate_days(days: int = Body(7, embed=True)):
    """
    Appends +7 days of resolved operations to DuckDB/BQ,
    auto-approves any pending actions for test verification,
    and triggers the Auditor agent to close verifying cases.
    """
    print(f"⏩ rd-runner: Simulating +{days} days of post-intervention operations...")
    generate_7_days_after()
    
    # Auto-approve pending approvals so they transition to verifying
    from api.main import STORE_STATE, approve_action
    for cid, c in STORE_STATE["cases"].items():
        for act in c.get("actions", []):
            if act.get("status") == "awaiting_approval":
                approve_action(act["action_id"])

    # Trigger audit over verifying cases
    audit_results = run_audit()
    return {
        "status": "completed",
        "simulated_days": days,
        "audited_cases": audit_results
    }

@app.post("/audit-verifying")
def run_audit():
    """Audits all cases currently in 'verifying' or 'awaiting_approval' status."""
    from api.main import STORE_STATE
    audited = []
    
    # Audit cases in in-process store state
    for cid, c in list(STORE_STATE["cases"].items()):
        if c.get("status") in ("verifying", "awaiting_approval"):
            res = audit_case(c)
            c["status"] = res.new_status
            c["rupee_recovered"] = res.rupee_recovered
            c["rupee_prevented"] = res.rupee_prevented
            STORE_STATE["cases"][cid] = c
            try:
                with httpx.Client(base_url=RD_API_URL, timeout=1.0) as client:
                    client.post("/cases", json=c)
            except Exception:
                pass
            audited.append({
                "case_id": c["case_id"],
                "new_status": res.new_status,
                "drop_pct": res.drop_pct,
                "rupee_prevented": res.rupee_prevented,
                "rupee_recovered": res.rupee_recovered
            })
        
    return audited

@app.get("/cases")
def list_cases():
    from api.main import STORE_STATE
    return list(STORE_STATE["cases"].values())

@app.post("/reset")
def reset_all():
    try:
        with httpx.Client(base_url=RD_API_URL, timeout=3.0) as client:
            client.post("/reset")
    except Exception:
        pass
    return {"status": "reset_done"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
