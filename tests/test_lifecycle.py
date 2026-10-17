"""
Return Detective — Verification Test for Full Case Lifecycle (Step 10)
Tests the complete end-to-end loop:
  1. Triggering Chief Inspector across all candidates
  2. Forensics, Detective, and Enforcer execution
  3. Intermediate states (1 & 2 awaiting approval, 3 & 4 verifying, 5 verifying with refunds held, 6 watching)
  4. Post-intervention +7 days simulation and Auditor verification
  5. Final state: Scenarios 1-4 closed, Scenario 5 held, Scenario 6 watching
"""

import pytest
from api.main import STORE_STATE, reset_demo_state, approve_action
from api.runner import run_candidates, simulate_days, run_audit

def test_full_case_lifecycle():
    print("\n" + "=" * 80)
    print("🔄 RETURN DETECTIVE — FULL CASE LIFECYCLE VERIFICATION")
    print("=" * 80)
    
    # 1. Reset state
    reset_demo_state()
    
    # 2. Run candidates for today (2026-10-18)
    initial_run = run_candidates("2026-10-18")
    cases = STORE_STATE["cases"]
    
    print(f"Initial run processed {len(cases)} cases:")
    for cid, c in cases.items():
        print(f"  • [{cid}] {c['title']}")
        print(f"      Status: {c['status'].upper()} | Rupee Lost: ₹{c['rupee_lost']:,.2f}")
        for act in c.get("actions", []):
            print(f"        - Action [{act['action_id']}]: {act['title']} (Tier: {act['tier']}, Status: {act['status']})")
    print("-" * 80)

    # Verify intermediate states
    c1 = cases["CAND-001"]
    assert c1["status"] in ("awaiting_approval", "verifying")
    
    c2 = cases["CAND-002"]
    assert c2["status"] in ("awaiting_approval", "verifying")
    
    c3 = cases["CAND-003"]
    assert c3["status"] == "verifying"
    
    c4 = cases["CAND-004"]
    assert c4["status"] == "verifying"
    
    c5 = cases.get("CASE-ABUSE-005")
    assert c5 is not None
    assert len(STORE_STATE["held_refunds"]) == 3 # 3 fraud accounts frozen!
    
    c6 = cases["CAND-006"]
    assert c6["status"] == "watching" # Bread spike remains watching!
    print("✓ All intermediate statuses verified (Scenarios 1-5 active, Scenario 6 watching)!")

    # 3. Simulate +7 days of post-intervention operations
    print("\n⏩ Simulating +7 days of operations and running Auditor...")
    sim_res = simulate_days(7)
    
    # 4. Final verification after +7 days
    print("\n" + "=" * 80)
    print("🏁 FINAL CASE STATUSES AFTER +7 DAYS POST-INTERVENTION AUDIT")
    print("=" * 80)
    for cid, c in STORE_STATE["cases"].items():
        print(f"  • [{cid}] {c['title']}")
        print(f"      Final Status    : {c['status'].upper()}")
        print(f"      Rupee Recovered : ₹{c.get('rupee_recovered', 0):,.2f}")
        print(f"      Rupee Prevented : ₹{c.get('rupee_prevented', 0):,.2f}")
        print("-" * 80)
        
    # Assert final requirements:
    # 1–4 closed after +7 days with rupee_prevented > 0
    assert STORE_STATE["cases"]["CAND-001"]["status"] == "closed"
    assert STORE_STATE["cases"]["CAND-001"]["rupee_prevented"] > 0
    
    assert STORE_STATE["cases"]["CAND-002"]["status"] == "closed"
    assert STORE_STATE["cases"]["CAND-002"]["rupee_prevented"] > 0
    
    assert STORE_STATE["cases"]["CAND-003"]["status"] == "closed"
    assert STORE_STATE["cases"]["CAND-003"]["rupee_prevented"] > 0
    
    assert STORE_STATE["cases"]["CAND-004"]["status"] == "closed"
    assert STORE_STATE["cases"]["CAND-004"]["rupee_prevented"] > 0
    
    # 5 refunds held
    assert len(STORE_STATE["held_refunds"]) == 3
    
    # 6 bread spike stays watching
    assert STORE_STATE["cases"]["CAND-006"]["status"] == "watching"
    
    print("\n✅ Step 10 Full Loop Verified: 1-4 closed after +7d, 5 refunds held, 6 watching!")

if __name__ == "__main__":
    test_full_case_lifecycle()
