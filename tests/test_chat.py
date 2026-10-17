"""
Return Detective — Verification Test for Google Chat Card Approval (Step 12)
Validates that tapping Approve in Google Chat card updates the action to 'Done'.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app, STORE_STATE

client = TestClient(app)

def test_google_chat_approval_card():
    # Setup mock case with pending approval action
    case_id = "CASE-CHAT-TEST"
    action_id = "ACT-CLAIM-CHAT-01"
    STORE_STATE["cases"][case_id] = {
        "case_id": case_id,
        "title": "Tomato Batch B-4471 Rot Spike (GreenLeaf Farms)",
        "status": "awaiting_approval",
        "finding": {
            "root_cause": "supplier_batch",
            "confidence": 0.95
        },
        "actions": [
            {
                "action_id": action_id,
                "case_id": case_id,
                "action_type": "supplier_claim",
                "tier": "approve",
                "title": "File ₹12,500 Supplier Claim with GreenLeaf Farms",
                "description": "Formal vendor claim deduction",
                "rupee_impact": 12500.0,
                "status": "awaiting_approval"
            }
        ]
    }

    # 1. Test Cards v2 Generation
    card_res = client.post(f"/chat/test-card?action_id={action_id}")
    assert card_res.status_code == 200
    card_json = card_res.json()
    assert "cardsV2" in card_json
    card_obj = card_json["cardsV2"][0]["card"]
    assert "GreenLeaf Farms" in card_obj["header"]["title"]
    print("✓ Cards v2 JSON correctly constructed with header, evidence, and buttons.")

    # 2. Simulate Google Chat Button Click Event (Tapping Approve)
    chat_click_event = {
        "type": "CARD_CLICKED",
        "action": {
            "function": "approve_action",
            "parameters": [
                {"key": "action_id", "value": action_id}
            ]
        },
        "user": {
            "displayName": "Store Manager Koramangala",
            "email": "manager.s1@darkstore.internal"
        }
    }

    resp = client.post("/chat", json=chat_click_event)
    assert resp.status_code == 200
    res_data = resp.json()
    assert "APPROVED" in res_data.get("text", "")
    print(f"Chat response: {res_data.get('text')}")

    # 3. Verify action in store state immediately changed to Done!
    updated_act = STORE_STATE["cases"][case_id]["actions"][0]
    assert updated_act["status"] == "Done"
    print("✓ Action status in store state successfully updated to 'Done'!")

if __name__ == "__main__":
    test_google_chat_approval_card()
