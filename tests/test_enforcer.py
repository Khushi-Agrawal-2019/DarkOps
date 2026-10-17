"""
Return Detective — Verification Test for The Enforcer Agent (Step 9)
Tests Scenario 1 execution:
  - 2 auto actions executed (Quarantine + Customer notify)
  - 1 approval action pending (Supplier claim)
  - GET /inventory/S1/B-4471 returns 0 sellable units
  - Supplier claim approval card waiting with drafted claim letter and evidence pack
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app, STORE_STATE
from agents.return_detective.sub_agents.detective import CaseFinding, RankedHypothesis
from agents.return_detective.sub_agents.enforcer import execute_enforcer

client = TestClient(app)

def test_scenario_1_enforcer():
    # Reset store state
    client.post("/reset")
    
    # 1. Create Scenario 1 CaseFinding
    finding = CaseFinding(
        candidate_id="CAND-001",
        root_cause="supplier_batch",
        confidence=0.95,
        ranked_hypotheses=[
            RankedHypothesis(cause="supplier_batch", confidence=0.95, summary="Supplier Batch Rot 13.6x baseline")
        ],
        summary_for_manager="Definitive evidence of supplier batch rot detected on Tomato Batch B-4471 from GreenLeaf Farms.",
        rupee_impact=76.0,
        evidence_payload={"batch_id": "B-4471", "supplier_name": "GreenLeaf Farms"}
    )
    
    case_id = "CASE-SCENARIO-1"
    store_ids = ["S1", "S2", "S3"]
    
    # 2. Execute Enforcer
    actions = execute_enforcer(finding, case_id, store_ids)
    
    print("\n" + "=" * 80)
    print("🛡️  THE ENFORCER — ACTION EXECUTION AUDIT (SCENARIO 1)")
    print("=" * 80)
    for act in actions:
        print(f"[{act.action_id}] {act.title}")
        print(f"  • Tier       : {act.tier.upper()}")
        print(f"  • Status     : {act.status}")
        print(f"  • Impact     : ₹{act.rupee_impact:,.2f}")
        print(f"  • Reversible : {act.reversible}")
        if act.draft_content:
            print("  • Drafted Supplier Claim Notice:")
            print("    " + "\n    ".join(act.draft_content.splitlines()[:6]))
        print("-" * 80)
        
    # Also save case into API
    case_doc = {
        "case_id": case_id,
        "title": "Tomato Batch B-4471 Rot Spike (GreenLeaf Farms)",
        "store_ids": store_ids,
        "status": "awaiting_approval",
        "actions": [act.model_dump() for act in actions]
    }
    client.post("/cases", json=case_doc)

    # 3. Assertions
    auto_actions = [a for a in actions if a.tier == "auto"]
    approve_actions = [a for a in actions if a.tier == "approve"]
    
    assert len(auto_actions) == 2, f"Expected 2 auto actions, got {len(auto_actions)}"
    assert len(approve_actions) == 1, f"Expected 1 approve action, got {len(approve_actions)}"
    assert approve_actions[0].status == "awaiting_approval"
    assert "GreenLeaf Farms" in approve_actions[0].draft_content

    # 4. Check inventory endpoint: GET /inventory/S1/B-4471 must return 0 sellable units!
    inv_res = client.get("/inventory/S1/B-4471")
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    print(f"Inventory S1/B-4471 Status: {inv_data}")
    assert inv_data["sellable_units"] == 0
    assert inv_data["is_quarantined"] is True
    
    # 5. Check other stores S2 and S3 are also quarantined
    assert client.get("/inventory/S2/B-4471").json()["sellable_units"] == 0
    assert client.get("/inventory/S3/B-4471").json()["sellable_units"] == 0
    
    # 6. Test Store Manager Approval Workflow
    claim_act_id = approve_actions[0].action_id
    appr_res = client.post(f"/actions/{claim_act_id}/approve", json={"approved_by": "Store Manager Koramangala"})
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "Done"
    print(f"Approved Action {claim_act_id}: Status changed to Done!")

    print("\n✅ Step 9 Enforcer and Mock Store Action API Complete & Verified!")

if __name__ == "__main__":
    test_scenario_1_enforcer()
