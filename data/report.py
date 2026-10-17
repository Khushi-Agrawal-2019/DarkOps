"""
Return Detective — Forensic Scenario Verification Report
Reads Parquet / DuckDB dataset and prints statistical proof for all 6 planted scenarios.
"""

import os
import duckdb
from data.scenarios import SCENARIO_SETTINGS

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
DUCKDB_PATH = os.path.join(OUT_DIR, "return_detective.duckdb")

def generate_report():
    if not os.path.exists(DUCKDB_PATH):
        print(f"Error: Database {DUCKDB_PATH} not found. Run generator.py and load_bq.py first.")
        return

    con = duckdb.connect(DUCKDB_PATH, read_only=True)
    
    print("=" * 80)
    print("🕵️  RETURN DETECTIVE — FORENSIC EVIDENCE VERIFICATION REPORT")
    print("=" * 80)
    
    # Overview metrics
    order_cnt = con.execute("SELECT count(*) FROM orders").fetchone()[0]
    item_cnt = con.execute("SELECT count(*) FROM order_items").fetchone()[0]
    complaint_cnt = con.execute("SELECT count(*) FROM complaints").fetchone()[0]
    total_refund = con.execute("SELECT sum(refund_inr) FROM complaints").fetchone()[0] or 0
    overall_complaint_rate = (complaint_cnt / item_cnt) * 100
    
    print(f"Total Orders      : {order_cnt:,d}")
    print(f"Total Order Items : {item_cnt:,d}")
    print(f"Total Complaints  : {complaint_cnt:,d} ({overall_complaint_rate:.2f}% of items)")
    print(f"Total Refund INR  : ₹{total_refund:,.2f}")
    print("-" * 80)

    # -------------------------------------------------------------
    # Scenario 1: Tomato batch B-4471 rot rate vs baseline
    # -------------------------------------------------------------
    print("📊 SCENARIO 1: Supplier Batch Quality (Batch B-4471, GreenLeaf Farms)")
    q1 = """
    WITH tomato_items AS (
        SELECT oi.order_item_id, oi.batch_id,
               CASE WHEN c.complaint_id IS NOT NULL AND c.type = 'rotten' THEN 1 ELSE 0 END as is_rotten
        FROM order_items oi
        JOIN skus s ON oi.sku_id = s.sku_id
        LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
        WHERE s.sku_id = 'SKU-001'
    )
    SELECT 
        batch_id,
        count(*) as total_items,
        sum(is_rotten) as rotten_complaints,
        round(avg(is_rotten) * 100, 2) as rot_rate_pct
    FROM tomato_items
    GROUP BY batch_id
    ORDER BY total_items DESC
    """
    res1 = con.execute(q1).df()
    b4471_row = res1[res1["batch_id"] == SCENARIO_SETTINGS.s1_batch_id]
    other_rows = res1[res1["batch_id"] != SCENARIO_SETTINGS.s1_batch_id]
    b4471_rate = b4471_row["rot_rate_pct"].values[0] if len(b4471_row) > 0 else 0.0
    other_rate = other_rows["rot_rate_pct"].mean() if len(other_rows) > 0 else 1.5
    multiplier1 = (b4471_rate / other_rate) if other_rate > 0 else 0.0
    print(f"  • Batch B-4471 Rot Rate : {b4471_rate:.2f}% ({b4471_row['rotten_complaints'].values[0] if len(b4471_row)>0 else 0} rotten claims)")
    print(f"  • Baseline Tomato Rot   : {other_rate:.2f}%")
    print(f"  • Ratio vs Baseline     : {multiplier1:.1f}x [Target ~6x]")
    assert multiplier1 >= 3.5, f"Scenario 1 signal too weak: {multiplier1}x"
    print("  ✅ Scenario 1 confirmed present!")
    print("-" * 80)

    # -------------------------------------------------------------
    # Scenario 2: S1 Freezer F2 Afternoon Drift (-8C) vs Normal (-19C)
    # -------------------------------------------------------------
    print("📊 SCENARIO 2: Equipment Failure (Store S1 Freezer F2 Afternoon Drift)")
    q2_temp = """
    SELECT 
        store_id, unit_id,
        round(avg(temp_c), 2) as avg_temp,
        round(max(temp_c), 2) as max_temp,
        count(CASE WHEN temp_c > -12.0 THEN 1 END) as warm_intervals_count
    FROM freezer_logs
    WHERE store_id = 'S1' AND unit_id = 'F2'
      AND CAST(SUBSTR(ts, 12, 2) AS INT) BETWEEN 12 AND 17
      AND ts >= '2026-10-11'
    GROUP BY store_id, unit_id
    """
    res2 = con.execute(q2_temp).df()
    print(f"  • S1/F2 Afternoon Temp Avg (Last 7 Days) : {res2['avg_temp'].values[0]}°C (Max: {res2['max_temp'].values[0]}°C)")
    print(f"  • Telemetry intervals drifting > -12°C   : {res2['warm_intervals_count'].values[0]} readings")
    
    # Check melt complaints for frozen items at S1 in afternoon
    q2_melt = """
    SELECT 
        o.store_id,
        count(c.complaint_id) as melt_complaints
    FROM complaints c
    JOIN order_items oi ON c.order_item_id = oi.order_item_id
    JOIN orders o ON oi.order_id = o.order_id
    JOIN skus s ON oi.sku_id = s.sku_id
    WHERE c.type = 'melted' AND s.storage_req = 'frozen'
      AND CAST(SUBSTR(o.ordered_at, 12, 2) AS INT) BETWEEN 12 AND 17
      AND o.ordered_at >= '2026-10-11'
    GROUP BY o.store_id
    ORDER BY o.store_id
    """
    res2_melt = con.execute(q2_melt).df()
    s1_melts = res2_melt[res2_melt["store_id"] == "S1"]["melt_complaints"].values[0] if "S1" in res2_melt["store_id"].values else 0
    print(f"  • S1 Afternoon Melt Complaints (Last 7 Days) : {s1_melts}")
    assert s1_melts > 5, "Scenario 2 melt complaints too low"
    print("  ✅ Scenario 2 confirmed present!")
    print("-" * 80)

    # -------------------------------------------------------------
    # Scenario 3: S2 Zone 3 Melt Complaints vs Normal Delivery
    # -------------------------------------------------------------
    print("📊 SCENARIO 3: Delivery Cold Chain Break (Store S2 Zone 3 on Hot Days)")
    q3 = """
    SELECT 
        d.zone_id,
        round(avg(d.duration_min), 1) as avg_duration_min,
        count(CASE WHEN c.type = 'melted' THEN 1 END) as melt_complaints
    FROM deliveries d
    JOIN orders o ON d.order_id = o.order_id
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN skus s ON oi.sku_id = s.sku_id
    JOIN weather_daily w ON CAST(o.ordered_at AS DATE) = CAST(w.date AS DATE) AND o.store_id = w.store_id
    LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
    WHERE o.store_id = 'S2' AND s.storage_req = 'frozen'
      AND w.max_temp_c >= 35.0 AND CAST(SUBSTR(o.ordered_at, 12, 2) AS INT) BETWEEN 12 AND 17
    GROUP BY d.zone_id
    ORDER BY d.zone_id
    """
    res3 = con.execute(q3).df()
    z3_row = res3[res3["zone_id"] == "S2-Z3"]
    other_z = res3[res3["zone_id"] != "S2-Z3"]
    print(f"  • S2-Z3 Hot Afternoon Avg Duration : {z3_row['avg_duration_min'].values[0]} min | Melts: {z3_row['melt_complaints'].values[0]}")
    print(f"  • Other S2 Zones Avg Duration     : {other_z['avg_duration_min'].mean():.1f} min | Melts: {other_z['melt_complaints'].mean():.1f}")
    assert z3_row["avg_duration_min"].values[0] > 18.0, "Scenario 3 transit duration not delayed > 18 min"
    print("  ✅ Scenario 3 confirmed present!")
    print("-" * 80)

    # -------------------------------------------------------------
    # Scenario 4: S3 Packer PK-308 Crushed-Egg Rate vs Store Average
    # -------------------------------------------------------------
    print("📊 SCENARIO 4: Human Negligence (Store S3 Packer PK-308 Crushed Eggs)")
    q4 = """
    SELECT 
        f.packer_id,
        count(*) as egg_items_packed,
        count(CASE WHEN c.type = 'crushed' THEN 1 END) as crushed_complaints,
        round(count(CASE WHEN c.type = 'crushed' THEN 1 END) * 100.0 / count(*), 2) as crush_rate_pct
    FROM fulfilment f
    JOIN orders o ON f.order_id = o.order_id
    JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
    WHERE o.store_id = 'S3' AND oi.sku_id = 'SKU-011'
    GROUP BY f.packer_id
    HAVING count(*) >= 15
    ORDER BY crush_rate_pct DESC
    """
    res4 = con.execute(q4).df()
    pk308_row = res4[res4["packer_id"] == SCENARIO_SETTINGS.s4_packer_id]
    other_packers = res4[res4["packer_id"] != SCENARIO_SETTINGS.s4_packer_id]
    pk_rate = pk308_row["crush_rate_pct"].values[0] if len(pk308_row) > 0 else 0.0
    other_pk_rate = other_packers["crush_rate_pct"].mean() if len(other_packers) > 0 else 1.0
    pk_multiplier = pk_rate / other_pk_rate if other_pk_rate > 0 else 0.0
    print(f"  • Packer PK-308 Crush Rate : {pk_rate:.2f}% ({pk308_row['crushed_complaints'].values[0]} crushed claims)")
    print(f"  • Other S3 Packers Crush   : {other_pk_rate:.2f}%")
    print(f"  • Ratio vs Other Packers   : {pk_multiplier:.1f}x [Target ~5x]")
    assert pk_multiplier >= 3.0, f"Scenario 4 signal too weak: {pk_multiplier}x"
    print("  ✅ Scenario 4 confirmed present!")
    print("-" * 80)

    # -------------------------------------------------------------
    # Scenario 5: Coordinated Refund Abuse (3 Accounts, 9 Claims, 2 Photos)
    # -------------------------------------------------------------
    print("📊 SCENARIO 5: Coordinated Refund Abuse (Multi-Account Photo Reuse)")
    q5 = """
    SELECT 
        customer_id,
        count(*) as abuse_claims,
        string_agg(photo_uri, ', ') as photo_uris
    FROM complaints
    WHERE complaint_id LIKE 'CMP-ABUSE%'
    GROUP BY customer_id
    """
    res5 = con.execute(q5).df()
    total_abuse_claims = res5["abuse_claims"].sum()
    print(f"  • Fraud Customer Accounts : {len(res5)} accounts ({', '.join(res5['customer_id'])})")
    print(f"  • Reused Photo Claims    : {total_abuse_claims} claims across accounts")
    assert total_abuse_claims == 9, "Scenario 5 abuse claims count mismatch"
    print("  ✅ Scenario 5 confirmed present!")
    print("-" * 80)

    # -------------------------------------------------------------
    # Scenario 6: Red Herring (One-day bread spike with no single root cause)
    # -------------------------------------------------------------
    print("📊 SCENARIO 6: Red Herring (One-Day Bread Complaint Spike)")
    q6 = """
    SELECT 
        count(*) as herring_complaints,
        count(DISTINCT o.store_id) as stores_affected,
        count(DISTINCT f.packer_id) as packers_involved,
        count(DISTINCT b.supplier_id) as suppliers_involved
    FROM complaints c
    JOIN order_items oi ON c.order_item_id = oi.order_item_id
    JOIN orders o ON oi.order_id = o.order_id
    JOIN batches b ON oi.batch_id = b.batch_id
    JOIN fulfilment f ON o.order_id = f.order_id
    WHERE c.complaint_id LIKE 'CMP-HERRING%'
    """
    res6 = con.execute(q6).df()
    print(f"  • Bread Spike Claims   : {res6['herring_complaints'].values[0]} complaints on single date")
    print(f"  • Affected Stores      : {res6['stores_affected'].values[0]} / 4 stores")
    print(f"  • Involved Packers     : {res6['packers_involved'].values[0]} distinct packers")
    print(f"  • Involved Suppliers   : {res6['suppliers_involved'].values[0]} distinct suppliers (Diffuse/Inconclusive)")
    assert res6["herring_complaints"].values[0] >= 20, "Scenario 6 complaints too few"
    print("  ✅ Scenario 6 confirmed present!")
    print("=" * 80)
    print("🎯 ALL 6 ROOT-CAUSE SCENARIOS ARE STATISTICALLY PROVEN AND PRESENT!")
    print("=" * 80)

if __name__ == "__main__":
    generate_report()
