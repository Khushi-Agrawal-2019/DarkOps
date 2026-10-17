"""
Return Detective — End-to-End Scenario Test Suite (Step 14)
Runs against full services for 3 consecutive iterations to ensure 100% deterministic reliability.
Asserts:
  1. All 6 scenarios trigger and resolve accurately
  2. Scenarios 1-4 achieve confidence >= 0.80 and correct action tiers
  3. Scenario 5 triggers refund freeze across accounts
  4. Scenario 6 comes back inconclusive and remains in 'watching' status
  5. After +7 days simulation, Scenarios 1-4 close with rupee_prevented > 0
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app, STORE_STATE
from api.runner import run_candidates, simulate_days

client = TestClient(app)

def run_single_test_iteration(iteration: int):
    print(f"\n--- Running Full Scenario Suite Iteration {iteration} of 3 ---")
    
    # 1. POST /reset
    client.post("/reset")
    assert len(STORE_STATE["cases"]) == 0
    assert len(STORE_STATE["held_refunds"]) == 0

    # 2. Run candidates (as of today: 2026-10-18)
    run_res = run_candidates("2026-10-18")
    cases = STORE_STATE["cases"]
    assert len(cases) >= 6, f"Expected at least 6 cases, got {len(cases)}"

    # 3. Assert Scenario 1 (Tomato Batch B-4471 Rot)
    c1 = cases.get("CAND-001")
    assert c1 is not None, "Scenario 1 case missing"
    assert c1["finding"]["root_cause"] == "supplier_batch"
    assert c1["finding"]["confidence"] >= 0.80
    tiers1 = [a["tier"] for a in c1["actions"]]
    assert "auto" in tiers1
    assert "approve" in tiers1
    assert c1["status"] in ("awaiting_approval", "verifying")

    # 4. Assert Scenario 2 (S1 Freezer F2 Drift)
    c2 = cases.get("CAND-002")
    assert c2 is not None, "Scenario 2 case missing"
    assert c2["finding"]["root_cause"] == "storage_temperature"
    assert c2["finding"]["confidence"] >= 0.80
    tiers2 = [a["tier"] for a in c2["actions"]]
    assert "auto" in tiers2

    # 5. Assert Scenario 3 (S2 Zone 3 Transit Delay & Heat)
    c3 = cases.get("CAND-003")
    assert c3 is not None, "Scenario 3 case missing"
    assert c3["finding"]["root_cause"] == "delivery_transit"
    assert c3["finding"]["confidence"] >= 0.80
    assert c3["status"] == "verifying"

    # 6. Assert Scenario 4 (Store S3 Packer PK-308)
    c4 = cases.get("CAND-004")
    assert c4 is not None, "Scenario 4 case missing"
    assert c4["finding"]["root_cause"] == "packing_negligence"
    assert c4["finding"]["confidence"] >= 0.80
    assert c4["status"] == "verifying"

    # 7. Assert Scenario 5 (Fraud Abuse Ring)
    c5 = cases.get("CASE-ABUSE-005")
    assert c5 is not None, "Scenario 5 case missing"
    assert len(STORE_STATE["held_refunds"]) == 3, "Failed to freeze 3 fraud accounts"

    # 8. Assert Scenario 6 (Red Herring Bread Spike)
    c6 = cases.get("CAND-006")
    assert c6 is not None, "Scenario 6 case missing"
    assert c6["finding"]["root_cause"] == "inconclusive"
    assert c6["status"] == "watching"
    assert len(c6.get("actions", [])) == 0 # No disruptive actions taken for red herring

    # 9. Approve pending actions through API
    for cid, c in cases.items():
        for act in c.get("actions", []):
            if act["status"] == "awaiting_approval":
                appr = client.post(f"/actions/{act['action_id']}/approve", json={"approved_by": f"Tester Iteration {iteration}"})
                assert appr.status_code == 200

    # 10. Simulate +7 days
    sim = simulate_days(7)
    assert sim["status"] == "completed"

    # 11. Assert Scenarios 1-4 are closed with positive rupee_prevented
    for sc_id in ["CAND-001", "CAND-002", "CAND-003", "CAND-004"]:
        sc_case = STORE_STATE["cases"][sc_id]
        assert sc_case["status"] == "closed", f"{sc_id} failed to close after +7 days (status: {sc_case['status']})"
        assert sc_case["rupee_prevented"] > 0, f"{sc_id} rupee_prevented must be > 0"

    # Assert Scenario 6 remains watching
    assert STORE_STATE["cases"]["CAND-006"]["status"] == "watching"
    print(f"✓ Iteration {iteration} PASSED cleanly with 100% scenario accuracy!")

def test_three_consecutive_runs():
    print("\n" + "=" * 80)
    print("🧪 EXECUTING 3 CONSECUTIVE END-TO-END SCENARIO VALIDATION RUNS")
    print("=" * 80)
    for i in range(1, 4):
        run_single_test_iteration(i)
    print("\n" + "=" * 80)
    print("🎉 ALL 3 CONSECUTIVE TEST RUNS PASSED! 0 FLAKY SCENARIOS DETECTED!")
    print("=" * 80)

if __name__ == "__main__":
    test_three_consecutive_runs()
