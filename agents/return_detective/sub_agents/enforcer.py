"""
Return Detective — The Enforcer Agent
Translates root-cause findings into operational actions using a fixed playbook.
Applies deterministic safety guardrails (policy.decide_tier):
  - 'auto': Executed immediately via mock store API (Cloud Run rd-api)
  - 'approve': Writes approval card to Firestore cases/{caseId}/actions/{actionId} (status: awaiting_approval)
  - 'recommend': Flagged for executive owner review
Drafts supplier claim packs, customer communications, and maintenance briefs with concrete evidence.
"""

import os
import uuid
import datetime
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from agents.return_detective.policy import decide_tier, ActionTier
from agents.return_detective.sub_agents.detective import CaseFinding

load_dotenv()

RD_API_URL = os.getenv("RD_API_URL", "http://localhost:8000")

class ProposedAction(BaseModel):
    action_id: str
    case_id: str
    action_type: str
    tier: ActionTier
    title: str
    description: str
    rupee_impact: float
    reversible: bool
    status: str # "Done", "awaiting_approval", "recommended", "Failed"
    undo_url: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    draft_content: Optional[str] = None # Draft email/claim text

def generate_supplier_claim_draft(finding: CaseFinding, batch_id: str = "B-4471") -> str:
    """Drafts formal supplier claim letter with forensic evidence pack."""
    return (
        f"FORMAL DEFECT CLAIM & RECOVERY NOTICE\n"
        f"To: Accounts & Quality Assurance, GreenLeaf Farms\n"
        f"Subject: Immediate Credit Note & Batch Recall Request — Tomato Batch {batch_id}\n\n"
        f"Dear Vendor Partner,\n\n"
        f"Our forensic quality audit system (Return Detective) has confirmed an anomalous rot failure in Batch {batch_id} "
        f"received across Koramangala (S1), Indiranagar (S2), and HSR Layout (S3) dark stores.\n\n"
        f"EVIDENCE SUMMARY:\n"
        f"1. Customer complaint rot rate: 13.6x higher than SKU baseline benchmark.\n"
        f"2. Physical visual audit: Gemini Flash inspection confirmed fungal rot on multiple customer return photos.\n"
        f"3. Storage audit: Dark store temperature logs confirmed consistent optimal conditions (freezer/chiller normal).\n\n"
        f"CLAIM AMOUNT: ₹12,500.00 (includes unsellable quarantined units and customer goodwill refunds).\n"
        f"Action Required: Please acknowledge receipt and credit our vendor account within 5 business days.\n\n"
        f"Operations Quality Team, Quick-Commerce Logistics"
    )

def execute_enforcer(finding: CaseFinding, case_id: str, store_ids: List[str]) -> List[ProposedAction]:
    """
    Executes the Enforcer playbook for the given CaseFinding:
    Determines action tiers, fires auto actions via rd-api, and enqueues approval actions.
    """
    actions: List[ProposedAction] = []
    cause = finding.root_cause
    
    # --------------------------------------------------------------------------
    # Playbook: Supplier Batch (Scenario 1)
    # --------------------------------------------------------------------------
    if cause == "supplier_batch":
        batch_id = "B-4471"
        claim_draft = generate_supplier_claim_draft(finding, batch_id)
        
        # Action 1: Quarantine Batch in All Stores (Auto)
        act1_id = f"ACT-QUAR-{uuid.uuid4().hex[:6].upper()}"
        tier1 = decide_tier("inventory_quarantine", finding.confidence, reversible=True, rupee_impact=finding.rupee_impact)
        actions.append(ProposedAction(
            action_id=act1_id,
            case_id=case_id,
            action_type="inventory_quarantine",
            tier=tier1,
            title=f"Quarantine Batch {batch_id} Inventory",
            description=f"Instantly set sellable units to 0 for batch {batch_id} across dark stores {', '.join(store_ids)} to halt bad dispatches.",
            rupee_impact=finding.rupee_impact,
            reversible=True,
            status="Done" if tier1 == "auto" else "awaiting_approval",
            undo_url=f"{RD_API_URL}/inventory/release",
            evidence={"batch_id": batch_id, "stores": store_ids, "quarantine_reason": "Rot complaint spike"}
        ))
        
        # Action 2: Customer Apology & Proactive Credit (Auto)
        act2_id = f"ACT-NOTIF-{uuid.uuid4().hex[:6].upper()}"
        tier2 = decide_tier("customer_notify", finding.confidence, reversible=True, rupee_impact=0.0)
        actions.append(ProposedAction(
            action_id=act2_id,
            case_id=case_id,
            action_type="customer_notify",
            tier=tier2,
            title="Send Apology & Wallet Credit to Affected Customers",
            description="Automated in-app notification apologizing for spoiled tomatoes with ₹50 courtesy wallet credit.",
            rupee_impact=0.0,
            reversible=True,
            status="Done" if tier2 == "auto" else "awaiting_approval",
            undo_url=f"{RD_API_URL}/customers/notify/recall",
            evidence={"channels": ["push_notification", "sms"], "affected_customers": 7}
        ))
        
        # Action 3: Supplier Claim & Evidence Pack (Needs Store Manager Approval)
        act3_id = f"ACT-CLAIM-{uuid.uuid4().hex[:6].upper()}"
        tier3 = decide_tier("supplier_claim", finding.confidence, reversible=False, rupee_impact=12500.0)
        actions.append(ProposedAction(
            action_id=act3_id,
            case_id=case_id,
            action_type="supplier_claim",
            tier=tier3, # "approve"
            title="File ₹12,500 Supplier Claim with GreenLeaf Farms",
            description="Submit formal vendor defect deduction with forensic photo evidence pack to GreenLeaf Farms accounts.",
            rupee_impact=12500.0,
            reversible=False,
            status="awaiting_approval",
            undo_url=None,
            draft_content=claim_draft,
            evidence={"supplier_name": "GreenLeaf Farms", "batch_id": batch_id, "recovery_target_inr": 12500.0}
        ))

    # --------------------------------------------------------------------------
    # Playbook: Storage Temperature (Scenario 2)
    # --------------------------------------------------------------------------
    elif cause == "storage_temperature":
        act1_id = f"ACT-MNT-{uuid.uuid4().hex[:6].upper()}"
        tier1 = decide_tier("maintenance_ticket", finding.confidence, reversible=True, rupee_impact=2500.0)
        actions.append(ProposedAction(
            action_id=act1_id,
            case_id=case_id,
            action_type="maintenance_ticket",
            tier=tier1,
            title="Dispatch Urgent HVAC Technician for S1 Freezer F2",
            description="Book priority maintenance technician ticket to inspect compressor coolant leak on unit F2.",
            rupee_impact=2500.0,
            reversible=True,
            status="Done" if tier1 == "auto" else "awaiting_approval",
            undo_url=f"{RD_API_URL}/maintenance/tickets/cancel",
            evidence={"unit_id": "F2", "store_id": "S1", "drift_temp": "-8°C"}
        ))
        
        act2_id = f"ACT-REFUND-{uuid.uuid4().hex[:6].upper()}"
        tier2 = decide_tier("proactive_refund", finding.confidence, reversible=False, rupee_impact=1422.0)
        actions.append(ProposedAction(
            action_id=act2_id,
            case_id=case_id,
            action_type="proactive_refund",
            tier=tier2,
            title="Issue Proactive Refunds for Afternoon Ice Cream Orders",
            description="Proactively refund ₹1,422 to 6 customers who received thawed items during afternoon drift window.",
            rupee_impact=1422.0,
            reversible=False,
            status="awaiting_approval",
            evidence={"store_id": "S1", "refund_amount_inr": 1422.0, "time_window": "12 PM - 5 PM"}
        ))

    # --------------------------------------------------------------------------
    # Playbook: Delivery Transit (Scenario 3)
    # --------------------------------------------------------------------------
    elif cause == "delivery_transit":
        act1_id = f"ACT-ROUTE-{uuid.uuid4().hex[:6].upper()}"
        tier1 = decide_tier("ops_routing_rules", finding.confidence, reversible=True, rupee_impact=0.0)
        actions.append(ProposedAction(
            action_id=act1_id,
            case_id=case_id,
            action_type="ops_routing_rules",
            tier=tier1,
            title="Apply Heatwave Routing & Thermal Liner Rule for S2-Z3",
            description="Cap S2-Z3 delivery batching to max 12 mins transit and mandate frozen thermal bubble bags during 12-5 PM.",
            rupee_impact=0.0,
            reversible=True,
            status="Done",
            undo_url=f"{RD_API_URL}/ops/routing-rules/reset",
            evidence={"zone_id": "S2-Z3", "max_temp_c": 36.2, "transit_cap_min": 12.0}
        ))

    # --------------------------------------------------------------------------
    # Playbook: Packing Negligence (Scenario 4)
    # --------------------------------------------------------------------------
    elif cause == "packing_negligence":
        act1_id = f"ACT-PACK-{uuid.uuid4().hex[:6].upper()}"
        tier1 = decide_tier("ops_packing_rules", finding.confidence, reversible=True, rupee_impact=0.0)
        actions.append(ProposedAction(
            action_id=act1_id,
            case_id=case_id,
            action_type="ops_packing_rules",
            tier=tier1,
            title="Mandate Egg Tray Bubble Wrap & PK-308 Retraining",
            description="Add mandatory barcode scan for egg protective cushion wrap and assign shift supervisor retraining for PK-308.",
            rupee_impact=0.0,
            reversible=True,
            status="Done",
            evidence={"packer_id": "PK-308", "store_id": "S3", "crush_rate": "22%"}
        ))

    # --------------------------------------------------------------------------
    # Playbook: Refund Abuse (Scenario 5)
    # --------------------------------------------------------------------------
    elif cause == "refund_abuse":
        act1_id = f"ACT-HOLD-{uuid.uuid4().hex[:6].upper()}"
        tier1 = decide_tier("refunds_hold", finding.confidence, reversible=True, rupee_impact=0.0)
        actions.append(ProposedAction(
            action_id=act1_id,
            case_id=case_id,
            action_type="refunds_hold",
            tier=tier1,
            title="Freeze Pending Refunds on 3 Duplicate Photo Accounts",
            description="Halt instant UPI payout for accounts CUST-ABUSE-101, 102, 103 pending physical fraud review.",
            rupee_impact=0.0,
            reversible=True,
            status="Done",
            undo_url=f"{RD_API_URL}/refunds/release",
            evidence={"accounts": ["CUST-ABUSE-101", "CUST-ABUSE-102", "CUST-ABUSE-103"], "duplicate_claims": 9}
        ))
        
        act2_id = f"ACT-BAN-{uuid.uuid4().hex[:6].upper()}"
        tier2 = decide_tier("permanent_account_ban", finding.confidence, reversible=False, rupee_impact=0.0)
        actions.append(ProposedAction(
            action_id=act2_id,
            case_id=case_id,
            action_type="permanent_account_ban",
            tier=tier2, # "recommend"
            title="Blacklist Fraud Ring Devices & Payment Handles",
            description="Permanent blacklisting recommendation submitted to Chief Risk Officer / Store Owner.",
            rupee_impact=0.0,
            reversible=False,
            status="recommended",
            evidence={"action": "device_fingerprint_block"}
        ))

    # --------------------------------------------------------------------------
    # Dispatch Auto Actions to rd-api (HTTP or in-process)
    # --------------------------------------------------------------------------
    from api.main import (
        quarantine_inventory, notify_customers, hold_refunds,
        QuarantineRequest, CustomerNotifyRequest, RefundHoldRequest
    )
    
    for act in actions:
        if act.tier == "auto" and act.status == "Done":
            dispatched = False
            try:
                with httpx.Client(base_url=RD_API_URL, timeout=1.0) as http_client:
                    if act.action_type == "inventory_quarantine":
                        r = http_client.post("/inventory/quarantine", json={
                            "batch_id": act.evidence.get("batch_id", "B-4471"),
                            "store_ids": act.evidence.get("stores", ["S1", "S2", "S3"]),
                            "case_id": case_id
                        })
                        dispatched = (r.status_code == 200)
                    elif act.action_type == "customer_notify":
                        r = http_client.post("/customers/notify", json={
                            "customer_ids": ["CUST-001", "CUST-002"],
                            "case_id": case_id,
                            "message": act.description
                        })
                        dispatched = (r.status_code == 200)
            except Exception:
                dispatched = False

            # In-process direct execution fallback for unit tests and local CLI
            if not dispatched:
                if act.action_type == "inventory_quarantine":
                    quarantine_inventory(QuarantineRequest(
                        batch_id=act.evidence.get("batch_id", "B-4471"),
                        store_ids=act.evidence.get("stores", ["S1", "S2", "S3"]),
                        case_id=case_id
                    ))
                elif act.action_type == "customer_notify":
                    notify_customers(CustomerNotifyRequest(
                        customer_ids=["CUST-001", "CUST-002"],
                        case_id=case_id,
                        message=act.description
                    ))
                elif act.action_type == "refunds_hold":
                    hold_refunds(RefundHoldRequest(
                        customer_ids=act.evidence.get("accounts", []),
                        case_id=case_id,
                        reason="Duplicate photo detection"
                    ))

    return actions
