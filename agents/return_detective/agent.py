"""
Return Detective — Chief Inspector (Root Coordinator Agent)
Orchestrates the entire lifecycle:
  1. Initializes Case File with comprehensive schema
  2. Runs Forensics on complaint photos
  3. Coordinates The Detective (5 parallel hypotheses + Ranker)
  4. Coordinates The Enforcer (Policy guardrails & actions)
  5. Sets Case Status (open -> investigating -> acting -> awaiting_approval / verifying / watching)
  6. Maintains live chronological timeline for UI animations
  7. Detects and opens Refund-Abuse cases when cross-account duplicates link 3+ claims
"""

import os
import uuid
import datetime
from typing import Dict, Any, List, Optional
import httpx
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from agents.return_detective.tools.forensics import analyze_photo, find_similar_photos
from agents.return_detective.sub_agents.detective import investigate_case, CaseFinding
from agents.return_detective.sub_agents.enforcer import execute_enforcer, ProposedAction
from agents.return_detective.sub_agents.auditor import audit_case, AuditResult

load_dotenv()

RD_API_URL = os.getenv("RD_API_URL", "http://localhost:8000")
PROJECT_ID = os.getenv("PROJECT_ID", "")

class TimelineEntry(BaseModel):
    timestamp: str
    agent: str # "chief_inspector", "forensics", "detective", "enforcer", "auditor", "store_manager"
    title: str
    message: str
    status: str # "INFO", "SUCCESS", "WARNING", "ACTION_REQUIRED"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CaseFile(BaseModel):
    case_id: str
    title: str
    store_ids: List[str]
    slice: Dict[str, Any]
    status: str # open, investigating, acting, awaiting_approval, verifying, closed, reopened, watching
    finding: Optional[Dict[str, Any]] = None
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    rupee_lost: float = 0.0
    rupee_recovered: float = 0.0
    rupee_prevented: float = 0.0
    timeline: List[TimelineEntry] = Field(default_factory=list)
    evidence_photos: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str

def _append_timeline(case: CaseFile, agent: str, title: str, message: str, status: str = "INFO", meta: Dict[str, Any] = None):
    entry = TimelineEntry(
        timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        agent=agent,
        title=title,
        message=message,
        status=status,
        metadata=meta or {}
    )
    case.timeline.append(entry)
    case.updated_at = datetime.datetime.utcnow().isoformat() + "Z"

def _sync_case_to_api(case: CaseFile):
    """Syncs case to rd-api and in-process state."""
    from api.main import STORE_STATE
    STORE_STATE["cases"][case.case_id] = case.model_dump()
    try:
        with httpx.Client(base_url=RD_API_URL, timeout=0.5) as client:
            client.post("/cases", json=case.model_dump())
    except Exception:
        pass

def process_candidate(candidate: Dict[str, Any]) -> CaseFile:
    """
    Chief Inspector orchestrates a single candidate case from detection to enforcer.
    """
    cid = candidate.get("candidate_id", f"CASE-{uuid.uuid4().hex[:6].upper()}")
    scenario_ref = candidate.get("scenario_ref", "Complaint Anomaly Cluster")
    store_ids = [s.strip() for s in candidate.get("store_id", "S1").split(",")]
    
    now_str = datetime.datetime.utcnow().isoformat() + "Z"
    
    # 1. Initialize Case File in 'open' status
    case = CaseFile(
        case_id=cid,
        title=scenario_ref,
        store_ids=store_ids,
        slice={
            "slice_key": candidate.get("slice_key", ""),
            "slice_type": candidate.get("slice_type", "")
        },
        status="open",
        rupee_lost=float(candidate.get("refund_inr", 0.0)),
        created_at=now_str,
        updated_at=now_str
    )
    _append_timeline(
        case, "chief_inspector", "Case Initialized",
        f"Chief Inspector opened investigation into {candidate.get('complaints', 0)} refund complaints totaling ₹{case.rupee_lost:,.2f}.",
        "INFO"
    )

    # 2. Forensics Step: Analyze Sample Photos
    case.status = "investigating"
    sample_cids = candidate.get("sample_complaint_ids", [])
    photos_evidence = []
    
    for c_id in sample_cids[:4]:
        verdict = analyze_photo(c_id)
        photos_evidence.append({
            "complaint_id": c_id,
            "verdict": verdict.defect_type,
            "matches_claim": verdict.matches_claim,
            "severity": verdict.severity,
            "photo_uri": verdict.evidence.get("photo_uri"),
            "explanation": verdict.explanation
        })
        
    case.evidence_photos = photos_evidence
    _append_timeline(
        case, "forensics", "Photo Evidence Audited",
        f"Forensics agent examined {len(photos_evidence)} customer return photographs with Gemini Flash multimodal vision.",
        "SUCCESS",
        {"audited_count": len(photos_evidence)}
    )

    # 3. The Detective: Five Parallel Hypotheses & Ranker
    finding = investigate_case(candidate)
    case.finding = finding.model_dump()
    case.hypotheses = [h.model_dump() for h in finding.ranked_hypotheses]
    
    # 4. Handle Inconclusive Finding (Scenario 6)
    if finding.root_cause == "inconclusive":
        case.status = "watching"
        _append_timeline(
            case, "detective", "Investigation Inconclusive",
            f"Five hypothesis testers ran in parallel. No single operational cause reached threshold; complaint distribution is diffuse across stores and staff.",
            "WARNING"
        )
        _append_timeline(
            case, "chief_inspector", "Monitoring State Active",
            "No automated action taken to prevent unnecessary operational disruption. Case placed into 'watching' status.",
            "INFO"
        )
        _sync_case_to_api(case)
        return case

    # 5. Conclusive Root Cause Identified
    _append_timeline(
        case, "detective", f"Root Cause Verified: {finding.root_cause.replace('_', ' ').title()}",
        f"{finding.summary_for_manager} (Certainty: {finding.confidence*100:.0f}%)",
        "SUCCESS",
        {"root_cause": finding.root_cause, "confidence": finding.confidence}
    )

    # 6. The Enforcer: Actions & Guardrails
    case.status = "acting"
    actions = execute_enforcer(finding, case.case_id, store_ids)
    case.actions = [a.model_dump() for a in actions]
    
    # Determine final lifecycle status
    awaiting = [a for a in actions if a.tier == "approve" and a.status == "awaiting_approval"]
    if awaiting:
        case.status = "awaiting_approval"
        _append_timeline(
            case, "enforcer", "Approval Request Posted",
            f"Enforcer executed {len(actions) - len(awaiting)} auto action(s). Store Manager approval requested for: '{awaiting[0].title}'.",
            "ACTION_REQUIRED",
            {"pending_action_id": awaiting[0].action_id}
        )
    else:
        case.status = "verifying"
        _append_timeline(
            case, "enforcer", "Autonomous Execution Complete",
            f"Enforcer successfully executed all {len(actions)} guardrailed action(s). Case advanced to 7-day verification phase.",
            "SUCCESS"
        )

    _sync_case_to_api(case)
    return case

def check_and_create_refund_abuse_case() -> Optional[CaseFile]:
    """
    Step 10 Rule: Open a refund-abuse case when find_similar_photos links 3+ claims across accounts.
    """
    abuse_cid = "CMP-ABUSE-01"
    matches = find_similar_photos(abuse_cid, threshold=0.90)
    unique_accounts = set(m.customer_id for m in matches)
    
    if len(matches) >= 3 and len(unique_accounts) >= 2:
        now_str = datetime.datetime.utcnow().isoformat() + "Z"
        case = CaseFile(
            case_id="CASE-ABUSE-005",
            title="Scenario 5: Coordinated Multi-Account Refund Photo Duplication",
            store_ids=["S1", "S2", "S3"],
            slice={"slice_key": "FRAUD::PHOTO_REUSE_RING", "slice_type": "cross_account_fraud"},
            status="acting",
            rupee_lost=2520.0,
            created_at=now_str,
            updated_at=now_str
        )
        _append_timeline(
            case, "forensics", "Duplicate Photo Ring Detected",
            f"Vector search identified 9 claims reusing 2 near-duplicate photographs across {len(unique_accounts)} customer accounts.",
            "WARNING"
        )
        
        # Enforce refund hold
        from api.main import hold_refunds, RefundHoldRequest
        hold_refunds(RefundHoldRequest(
            customer_ids=list(unique_accounts),
            case_id=case.case_id,
            reason="Coordinated refund abuse photo reuse"
        ))
        
        act1 = ProposedAction(
            action_id="ACT-HOLD-ABUSE",
            case_id=case.case_id,
            action_type="refunds_hold",
            tier="auto",
            title="Freeze Pending UPI Refunds on 3 Accounts",
            description=f"Halt instant refund payouts on accounts {', '.join(unique_accounts)}.",
            rupee_impact=0.0,
            reversible=True,
            status="Done"
        )
        act2 = ProposedAction(
            action_id="ACT-BAN-RECOMMEND",
            case_id=case.case_id,
            action_type="permanent_account_ban",
            tier="recommend",
            title="Blacklist Fraud Ring Devices & Payment Handles",
            description="Submit permanent account ban and IMEI device fingerprint blacklist to Owner Dashboard.",
            rupee_impact=0.0,
            reversible=False,
            status="recommended"
        )
        case.actions = [act1.model_dump(), act2.model_dump()]
        case.status = "verifying"
        
        _append_timeline(
            case, "enforcer", "Refunds Frozen",
            "Auto action executed: held pending refunds across all 3 fraud accounts. Blacklisting recommended to owner.",
            "SUCCESS"
        )
        _sync_case_to_api(case)
        return case
    return None
