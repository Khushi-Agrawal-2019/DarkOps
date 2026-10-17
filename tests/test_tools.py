"""
Return Detective — Unit Tests for Investigation Tools (Step 7)
Validates query_batch_complaints, query_freezer_logs, query_delivery_times,
query_packer_stats, query_customer_history, and get_weather for Scenarios 1-4.
"""

import pytest
from agents.return_detective.tools.bq_tools import (
    get_case_candidate,
    query_batch_complaints,
    query_freezer_logs,
    query_delivery_times,
    query_packer_stats,
    query_customer_history,
    get_weather
)

def test_scenario_1_batch_tool():
    """Validates B-4471 batch investigation tool."""
    res = query_batch_complaints("B-4471")
    assert "summary" in res
    assert "evidence" in res
    ev = res["evidence"]
    assert ev["batch_id"] == "B-4471"
    assert ev["supplier_name"] == "GreenLeaf Farms"
    assert ev["spike_ratio_vs_baseline"] > 3.0
    assert ev["total_refund_inr"] > 0

def test_scenario_2_freezer_drift_tool():
    """Validates S1/F2 freezer logs tool shows afternoon drift."""
    res = query_freezer_logs("S1", "F2", "2026-10-11", "2026-10-18")
    assert "summary" in res
    assert "evidence" in res
    ev = res["evidence"]
    assert ev["store_id"] == "S1"
    assert ev["unit_id"] == "F2"
    assert ev["is_thermal_drift_detected"] is True
    assert ev["max_temp_c"] > -10.0
    assert ev["minutes_above_minus_15c"] > 120

def test_scenario_3_delivery_times_tool():
    """Validates S2-Z3 delivery transit times on hot days."""
    res = query_delivery_times("S2", "S2-Z3", "2026-10-11", "2026-10-18")
    assert "summary" in res
    assert "evidence" in res
    ev = res["evidence"]
    assert ev["store_id"] == "S2"
    assert ev["zone_id"] == "S2-Z3"
    assert len(ev["breakdown"]) > 0

def test_scenario_4_packer_stats_tool():
    """Validates S3 packer stats tool highlights PK-308 crushed rate."""
    res = query_packer_stats("S3", "2026-10-11", "2026-10-18")
    assert "summary" in res
    assert "evidence" in res
    ev = res["evidence"]
    assert ev["store_id"] == "S3"
    assert ev["top_outlier_packer"] == "PK-308"
    assert ev["outlier_multiplier"] >= 3.0

def test_customer_history_fraud_account():
    """Validates fraud customer claim history in Scenario 5."""
    res = query_customer_history("CUST-ABUSE-101")
    assert "summary" in res
    assert "evidence" in res
    ev = res["evidence"]
    assert ev["claims_in_90_days"] >= 3
    assert ev["is_high_risk_account"] is True

def test_get_weather():
    """Validates ambient weather extraction."""
    res = get_weather("S2", "2026-10-16")
    assert "summary" in res
    assert "evidence" in res
    assert res["evidence"]["max_temp_c"] > 25.0
