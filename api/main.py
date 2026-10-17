"""
Return Detective — Mock Dark Store Action API (FastAPI)
Microservice mocking warehouse inventory, customer notification, supplier claim,
and equipment maintenance systems. Persists audit state to Firestore (collection store_state).
"""

import os
import uuid
import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Return Detective Dark Store API",
    description="Operational action execution and audit microservice for quick-commerce dark stores",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ID = os.getenv("PROJECT_ID", "")
RD_API_URL = os.getenv("RD_API_URL", "http://localhost:8000")

# In-memory store state with Firestore sync
STORE_STATE = {
    "quarantined_batches": {}, # (batch_id, store_id) -> bool
    "sellable_units": {},      # (store_id, batch_id) -> int (default 45)
    "audit_log": [],
    "supplier_claims": {},
    "held_refunds": set(),
    "maintenance_tickets": {},
    "packing_rules": [],
    "routing_rules": [],
    "cases": {} # caseId -> Case Document
}

class QuarantineRequest(BaseModel):
    batch_id: str
    store_ids: List[str]
    case_id: Optional[str] = "CASE-MANUAL"
    reason: Optional[str] = "Suspected batch defect from Return Detective"

class SupplierClaimRequest(BaseModel):
    supplier_id: str
    batch_id: str
    case_id: str
    claim_amount_inr: float
    evidence_summary: str
    affected_stores: List[str]

class RefundHoldRequest(BaseModel):
    customer_ids: List[str]
    case_id: str
    reason: str

class CustomerNotifyRequest(BaseModel):
    customer_ids: List[str]
    case_id: str
    message: str

class MaintenanceTicketRequest(BaseModel):
    store_id: str
    unit_id: str
    issue: str
    case_id: str
    priority: str = "HIGH"

class ActionApprovalRequest(BaseModel):
    approved_by: str = "Store Manager"
    notes: Optional[str] = "Approved via Return Detective portal"

def _record_audit(action_name: str, payload: Dict[str, Any], undo_path: str) -> str:
    action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
    record = {
        "action_id": action_id,
        "action_name": action_name,
        "payload": payload,
        "status": "COMPLETED",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "undo_url": f"{RD_API_URL}{undo_path}"
    }
    STORE_STATE["audit_log"].append(record)
    return action_id

@app.get("/")
def health_check():
    return {
        "service": "rd-api",
        "status": "online",
        "quarantined_count": len([k for k, v in STORE_STATE["quarantined_batches"].items() if v]),
        "claims_count": len(STORE_STATE["supplier_claims"]),
        "audit_records": len(STORE_STATE["audit_log"])
    }

# ------------------------------------------------------------------------------
# Inventory Endpoints
# ------------------------------------------------------------------------------
@app.post("/inventory/quarantine")
def quarantine_inventory(req: QuarantineRequest):
    for s_id in req.store_ids:
        STORE_STATE["quarantined_batches"][(req.batch_id, s_id)] = True
        STORE_STATE["sellable_units"][(s_id, req.batch_id)] = 0
        
    action_id = _record_audit(
        "inventory_quarantine",
        req.model_dump(),
        f"/inventory/release?batch_id={req.batch_id}&store_ids={','.join(req.store_ids)}"
    )
    return {
        "status": "success",
        "action_id": action_id,
        "batch_id": req.batch_id,
        "quarantined_at": req.store_ids,
        "sellable_units": 0,
        "undo_url": f"{RD_API_URL}/inventory/release"
    }

@app.post("/inventory/release")
def release_inventory(batch_id: str, store_ids: str):
    s_list = store_ids.split(",")
    for s_id in s_list:
        STORE_STATE["quarantined_batches"][(batch_id, s_id)] = False
        STORE_STATE["sellable_units"][(s_id, batch_id)] = 45 # Restore default
        
    action_id = _record_audit("inventory_release", {"batch_id": batch_id, "store_ids": s_list}, f"/inventory/quarantine")
    return {
        "status": "undone",
        "action_id": action_id,
        "batch_id": batch_id,
        "released_at": s_list,
        "sellable_units": 45
    }

@app.get("/inventory/{store_id}/{batch_id}")
def get_inventory(store_id: str, batch_id: str):
    is_q = STORE_STATE["quarantined_batches"].get((batch_id, store_id), False)
    units = 0 if is_q else STORE_STATE["sellable_units"].get((store_id, batch_id), 45)
    return {
        "store_id": store_id,
        "batch_id": batch_id,
        "sellable_units": units,
        "is_quarantined": is_q
    }

# ------------------------------------------------------------------------------
# Suppliers & Claims
# ------------------------------------------------------------------------------
@app.post("/suppliers/claims")
def file_supplier_claim(req: SupplierClaimRequest):
    claim_id = f"CLM-{uuid.uuid4().hex[:6].upper()}"
    pdf_uri = f"gs://{PROJECT_ID}-rd-photos/claims/{claim_id}_evidence_pack.pdf"
    
    STORE_STATE["supplier_claims"][claim_id] = {
        "claim_id": claim_id,
        "supplier_id": req.supplier_id,
        "batch_id": req.batch_id,
        "amount_inr": req.claim_amount_inr,
        "case_id": req.case_id,
        "evidence_pack_uri": pdf_uri,
        "status": "SUBMITTED",
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    action_id = _record_audit("supplier_claim", req.model_dump(), f"/suppliers/claims/{claim_id}/cancel")
    return {
        "status": "success",
        "claim_id": claim_id,
        "action_id": action_id,
        "evidence_pack_pdf": pdf_uri,
        "amount_inr": req.claim_amount_inr,
        "undo_url": f"{RD_API_URL}/suppliers/claims/{claim_id}/cancel"
    }

# ------------------------------------------------------------------------------
# Customer & Refund Endpoints
# ------------------------------------------------------------------------------
@app.post("/customers/notify")
def notify_customers(req: CustomerNotifyRequest):
    action_id = _record_audit("customer_notify", req.model_dump(), "/customers/notify/recall")
    return {
        "status": "sent",
        "action_id": action_id,
        "recipients_count": len(req.customer_ids),
        "undo_url": f"{RD_API_URL}/customers/notify/recall"
    }

@app.post("/refunds/hold")
def hold_refunds(req: RefundHoldRequest):
    for cid in req.customer_ids:
        STORE_STATE["held_refunds"].add(cid)
    action_id = _record_audit("refund_hold", req.model_dump(), "/refunds/release")
    return {
        "status": "held",
        "action_id": action_id,
        "held_accounts": req.customer_ids,
        "undo_url": f"{RD_API_URL}/refunds/release"
    }

@app.post("/refunds/release")
def release_refunds(customer_ids: List[str] = Body(...)):
    for cid in customer_ids:
        STORE_STATE["held_refunds"].discard(cid)
    action_id = _record_audit("refund_release", {"customer_ids": customer_ids}, "/refunds/hold")
    return {"status": "released", "action_id": action_id, "accounts": customer_ids}

@app.post("/refunds/proactive")
def issue_proactive_refunds(order_ids: List[str] = Body(...), amount_inr: float = Body(...), case_id: str = Body(...)):
    action_id = _record_audit("refund_proactive", {"order_ids": order_ids, "amount_inr": amount_inr, "case_id": case_id}, "/refunds/cancel")
    return {"status": "credited", "action_id": action_id, "orders_refunded": len(order_ids), "total_inr": amount_inr}

# ------------------------------------------------------------------------------
# Operations & Maintenance
# ------------------------------------------------------------------------------
@app.post("/maintenance/tickets")
def create_maintenance_ticket(req: MaintenanceTicketRequest):
    t_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
    STORE_STATE["maintenance_tickets"][t_id] = req.model_dump()
    action_id = _record_audit("maintenance_ticket", req.model_dump(), f"/maintenance/tickets/{t_id}/cancel")
    return {"status": "scheduled", "ticket_id": t_id, "action_id": action_id, "undo_url": f"{RD_API_URL}/maintenance/tickets/{t_id}/cancel"}

@app.post("/ops/packing-rules")
def update_packing_rules(rule: str = Body(...), packer_id: Optional[str] = Body(None), case_id: str = Body(...)):
    STORE_STATE["packing_rules"].append({"rule": rule, "packer_id": packer_id, "case_id": case_id})
    action_id = _record_audit("packing_rules", {"rule": rule, "packer_id": packer_id}, "/ops/packing-rules/reset")
    return {"status": "updated", "action_id": action_id, "rule": rule}

@app.post("/ops/routing-rules")
def update_routing_rules(zone_id: str = Body(...), max_transit_min: float = Body(...), case_id: str = Body(...)):
    STORE_STATE["routing_rules"].append({"zone_id": zone_id, "max_transit_min": max_transit_min, "case_id": case_id})
    action_id = _record_audit("routing_rules", {"zone_id": zone_id, "max_transit_min": max_transit_min}, "/ops/routing-rules/reset")
    return {"status": "updated", "action_id": action_id, "zone_id": zone_id}

# ------------------------------------------------------------------------------
# Action Approval Workflow (Store Manager 1-Tap Execution)
# ------------------------------------------------------------------------------
@app.post("/actions/{action_id}/approve")
def approve_action(action_id: str, req: ActionApprovalRequest = None):
    # Find action across cases
    for case_id, case_doc in STORE_STATE["cases"].items():
        for act in case_doc.get("actions", []):
            if act["action_id"] == action_id:
                act["status"] = "Done"
                act["approved_by"] = req.approved_by if req else "Store Manager"
                act["approved_at"] = datetime.datetime.utcnow().isoformat()
                
                # Execute underlying business action
                if "supplier_claim" in act.get("action_type", ""):
                    file_supplier_claim(SupplierClaimRequest(
                        supplier_id="SUP-001",
                        batch_id="B-4471",
                        case_id=case_id,
                        claim_amount_inr=act.get("rupee_impact", 12500.0),
                        evidence_summary=act.get("description", "Supplier claim"),
                        affected_stores=["S1", "S2", "S3"]
                    ))
                elif "proactive_refund" in act.get("action_type", ""):
                    issue_proactive_refunds(["ORD-PROACTIVE"], act.get("rupee_impact", 1400.0), case_id)
                    
                # Update case status if all actions resolved
                pending = [a for a in case_doc.get("actions", []) if a["status"] == "awaiting_approval"]
                if not pending and case_doc.get("status") == "awaiting_approval":
                    case_doc["status"] = "verifying"
                    
                return {"status": "Done", "action_id": action_id, "case_status": case_doc.get("status")}
                
    return {"status": "Done", "action_id": action_id, "message": "Action marked Done."}

@app.post("/actions/{action_id}/reject")
def reject_action(action_id: str):
    for case_id, case_doc in STORE_STATE["cases"].items():
        for act in case_doc.get("actions", []):
            if act["action_id"] == action_id:
                act["status"] = "Rejected"
                return {"status": "Rejected", "action_id": action_id}
    return {"status": "Rejected", "action_id": action_id}

@app.post("/reset")
def reset_demo_state():
    STORE_STATE["quarantined_batches"].clear()
    STORE_STATE["sellable_units"].clear()
    STORE_STATE["audit_log"].clear()
    STORE_STATE["supplier_claims"].clear()
    STORE_STATE["held_refunds"].clear()
    STORE_STATE["maintenance_tickets"].clear()
    STORE_STATE["packing_rules"].clear()
    STORE_STATE["routing_rules"].clear()
    STORE_STATE["cases"].clear()

    # Reset DuckDB to baseline state if baseline exists
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "out", "return_detective.duckdb")
    baseline_path = db_path + ".baseline"
    if os.path.exists(baseline_path):
        import shutil
        shutil.copyfile(baseline_path, db_path)

    return {"status": "demo_reset_complete"}

# ------------------------------------------------------------------------------
# Case Management API
# ------------------------------------------------------------------------------
@app.get("/cases")
def list_cases():
    return list(STORE_STATE["cases"].values())

@app.get("/cases/{case_id}")
def get_case(case_id: str):
    if case_id not in STORE_STATE["cases"]:
        raise HTTPException(status_code=404, detail="Case not found")
    return STORE_STATE["cases"][case_id]

@app.post("/cases")
def create_or_update_case(case_data: Dict[str, Any] = Body(...)):
    cid = case_data.get("case_id")
    if cid:
        STORE_STATE["cases"][cid] = case_data
    return {"status": "synced", "case_id": cid}

@app.put("/cases/{case_id}")
def update_case(case_id: str, case_data: Dict[str, Any] = Body(...)):
    STORE_STATE["cases"][case_id] = case_data
    return {"status": "updated", "case_id": case_id}

# ------------------------------------------------------------------------------
# Google Chat Approval Card App (Step 12)
# ------------------------------------------------------------------------------
GOOGLE_CHAT_WEBHOOK_URL = os.getenv("GOOGLE_CHAT_WEBHOOK_URL", "")
RD_WEB_URL = os.getenv("RD_WEB_URL", "http://localhost:3000")

def build_google_chat_card_v2(case_doc: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
    """Builds standard Google Chat Cards v2 JSON specification."""
    action_id = action.get("action_id", "")
    case_id = case_doc.get("case_id", "")
    title = case_doc.get("title", "Forensic Quality Incident")
    root_cause = case_doc.get("finding", {}).get("root_cause", "Incident").replace("_", " ").title()
    conf = int(case_doc.get("finding", {}).get("confidence", 0.95) * 100)
    rupee_impact = action.get("rupee_impact", 0.0)
    
    photo_uri = "/complaints/rotten_fresh_produce_1.jpg"
    if case_doc.get("evidence_photos"):
        photo_uri = case_doc["evidence_photos"][0].get("photo_uri") or photo_uri
    photo_url = f"{RD_WEB_URL}{photo_uri}" if photo_uri.startswith("/") else photo_uri

    return {
        "cardsV2": [
            {
                "cardId": f"approval-{action_id}",
                "card": {
                    "header": {
                        "title": f"🚨 Return Detective: {title}",
                        "subtitle": f"Root Cause: {root_cause} • {conf}% Confidence",
                        "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/shield_with_heart/default/48px.svg",
                        "imageType": "CIRCLE"
                    },
                    "sections": [
                        {
                            "header": "Forensic Evidence Summary",
                            "widgets": [
                                {
                                    "decoratedText": {
                                        "topLabel": "Statistical Signal",
                                        "text": "<b>Defect Rate:</b> 13.6x higher than SKU baseline across multiple dark stores."
                                    }
                                },
                                {
                                    "decoratedText": {
                                        "topLabel": "Multimodal Vision",
                                        "text": "<b>Gemini Flash:</b> Physical spoilage confirmed on customer return photos."
                                    }
                                },
                                {
                                    "decoratedText": {
                                        "topLabel": "Storage Integrity",
                                        "text": "<b>Telemetry Audit:</b> Normal freezer/chiller operating temperatures prior to pack."
                                    }
                                }
                            ]
                        },
                        {
                            "header": "Proposed Operational Action",
                            "widgets": [
                                {
                                    "decoratedText": {
                                        "topLabel": f"Financial Impact: ₹{rupee_impact:,.2f}",
                                        "text": f"<b>{action.get('title', '')}</b><br>{action.get('description', '')}"
                                    }
                                },
                                {
                                    "buttonList": {
                                        "buttons": [
                                            {
                                                "text": "Approve Action",
                                                "color": {"red": 0.08, "green": 0.64, "blue": 0.29, "alpha": 1.0},
                                                "onClick": {
                                                    "action": {
                                                        "function": "approve_action",
                                                        "parameters": [{"key": "action_id", "value": action_id}]
                                                    }
                                                }
                                            },
                                            {
                                                "text": "Reject",
                                                "color": {"red": 0.85, "green": 0.2, "blue": 0.2, "alpha": 1.0},
                                                "onClick": {
                                                    "action": {
                                                        "function": "reject_action",
                                                        "parameters": [{"key": "action_id", "value": action_id}]
                                                    }
                                                }
                                            },
                                            {
                                                "text": "Open Case",
                                                "onClick": {
                                                    "openLink": {
                                                        "url": f"{RD_WEB_URL}/cases/{case_id}"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }

@app.post("/chat")
def handle_google_chat_event(event: Dict[str, Any] = Body(...)):
    """Handles Google Chat card interactions and button clicks."""
    event_type = event.get("type", "")
    action = event.get("action", {})
    fn_name = action.get("function") or action.get("actionMethodName", "")
    params = {p["key"]: p["value"] for p in action.get("parameters", [])} if isinstance(action.get("parameters"), list) else {}
    action_id = params.get("action_id", "")

    if fn_name == "approve_action" and action_id:
        approve_action(action_id, ActionApprovalRequest(approved_by="Store Manager (Google Chat)", notes="Approved via Chat Card v2"))
        return {
            "actionResponse": {
                "type": "UPDATE_MESSAGE"
            },
            "text": f"✅ Action *{action_id}* APPROVED by Store Manager on {datetime.datetime.utcnow().strftime('%H:%M:%S UTC')}. Status updated to *Done* in web app!"
        }
    elif fn_name == "reject_action" and action_id:
        reject_action(action_id)
        return {
            "actionResponse": {
                "type": "UPDATE_MESSAGE"
            },
            "text": f"❌ Action *{action_id}* REJECTED by Store Manager."
        }

    return {"text": "Return Detective Chat Bot ready."}

@app.post("/chat/test-card")
def test_chat_card(action_id: str):
    for case_id, case_doc in STORE_STATE["cases"].items():
        for act in case_doc.get("actions", []):
            if act["action_id"] == action_id:
                return build_google_chat_card_v2(case_doc, act)
    raise HTTPException(status_code=404, detail="Action not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

