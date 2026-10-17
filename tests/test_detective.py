"""
Return Detective — Verification Test for The Detective Agent (Step 8)
Verifies that:
  - Scenario 1 identifies "supplier_batch" (confidence >= 0.8)
  - Scenario 2 identifies "storage_temperature" (confidence >= 0.8)
  - Scenario 3 identifies "delivery_transit" (freezer ruled out, confidence >= 0.8)
  - Scenario 4 identifies "packing_negligence" (confidence >= 0.8)
  - Scenario 6 comes back "inconclusive"
"""

import pytest
from sql.find_candidates import find_case_candidates
from agents.return_detective.sub_agents.detective import investigate_case

def test_detective_all_scenarios():
    df_candidates = find_case_candidates("2026-10-18")
    findings = {}

    print("\n" + "=" * 80)
    print("🕵️  THE DETECTIVE — HYPOTHESIS TESTING & RANKING RESULTS")
    print("=" * 80)

    for _, row in df_candidates.iterrows():
        cand = row.to_dict()
        cid = cand["candidate_id"]
        finding = investigate_case(cand)
        findings[cid] = finding

        print(f"[{cid}] Candidate: {cand['scenario_ref']}")
        print(f"  • Root Cause Found : {finding.root_cause.upper()}")
        print(f"  • Confidence Score : {finding.confidence*100:.1f}%")
        print(f"  • Rupee Impact     : ₹{finding.rupee_impact:,.2f}")
        print(f"  • Manager Summary  : {finding.summary_for_manager}")
        print("  • Hypothesis Rankings:")
        for rh in finding.ranked_hypotheses:
            print(f"      - {rh.summary}")
        print("-" * 80)

    # 1. Scenario 1 (CAND-001): supplier_batch
    f1 = findings["CAND-001"]
    assert f1.root_cause == "supplier_batch"
    assert f1.confidence >= 0.80

    # 2. Scenario 2 (CAND-002): storage_temperature
    f2 = findings["CAND-002"]
    assert f2.root_cause == "storage_temperature"
    assert f2.confidence >= 0.80

    # 3. Scenario 3 (CAND-003): delivery_transit (and freezer ruled out)
    f3 = findings["CAND-003"]
    assert f3.root_cause == "delivery_transit"
    assert f3.confidence >= 0.80
    # Check that storage was ruled out in ranked hypotheses
    storage_hyp = [rh for rh in f3.ranked_hypotheses if rh.cause == "storage_temperature"][0]
    assert "Ruled out" in storage_hyp.summary

    # 4. Scenario 4 (CAND-004): packing_negligence
    f4 = findings["CAND-004"]
    assert f4.root_cause == "packing_negligence"
    assert f4.confidence >= 0.80

    # 6. Scenario 6 (CAND-006): inconclusive
    f6 = findings["CAND-006"]
    assert f6.root_cause == "inconclusive"
    print("\n✅ All Detective Agent scenarios passed with expected root causes and confidence thresholds!")

if __name__ == "__main__":
    test_detective_all_scenarios()
