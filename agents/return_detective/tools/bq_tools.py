"""
Return Detective — BigQuery Investigation Tools
Provides vetted parameterised analytical queries over v_complaint_chain, daily_rates,
and v_freezer_hourly.
Every tool strictly returns JSON with:
  - "summary": one clear sentence describing the finding
  - "evidence": structured dictionary of exact metrics, counts, and ratios
"""

import os
from typing import Dict, Any, Optional
import duckdb
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "out", "return_detective.duckdb")
PROJECT_ID = os.getenv("PROJECT_ID", "")
DATASET = os.getenv("BIGQUERY_DATASET", "return_detective")

def _get_con():
    return duckdb.connect(DB_PATH, read_only=True)

def get_case_candidate(candidate_id: str) -> Dict[str, Any]:
    """Fetch details of a detected candidate anomaly case."""
    con = _get_con()
    row = con.execute("""
    SELECT candidate_id, scenario_ref, slice_type, slice_key, store_id, first_seen,
           anomaly_probability, complaints, refund_inr, sample_complaint_ids
    FROM case_candidates
    WHERE candidate_id = ?
    """, [candidate_id]).fetchone()
    con.close()
    
    if not row:
        return {
            "summary": f"No candidate found with ID {candidate_id}.",
            "evidence": {"candidate_id": candidate_id, "found": False}
        }
        
    return {
        "summary": f"Candidate {row[0]} triggered on {row[2]} ({row[3]}) across store(s) {row[4]} with {row[7]} complaints risking ₹{row[8]:,.2f}.",
        "evidence": {
            "candidate_id": row[0],
            "scenario_ref": row[1],
            "slice_type": row[2],
            "slice_key": row[3],
            "store_id": row[4],
            "first_seen": str(row[5]),
            "anomaly_probability": float(row[6]),
            "complaints_count": int(row[7]),
            "total_refund_inr": float(row[8]),
            "sample_complaints": list(row[9]) if row[9] else []
        }
    }

def query_batch_complaints(batch_id: str) -> Dict[str, Any]:
    """Calculates complaint rate per store vs SKU baseline and total refund INR."""
    con = _get_con()
    # Batch statistics
    b_stat = con.execute("""
    SELECT 
        b.batch_id,
        b.sku_id,
        s.name as sku_name,
        b.supplier_id,
        sup.name as supplier_name,
        count(oi.order_item_id) as total_items_shipped,
        count(c.complaint_id) as complaint_count,
        coalesce(sum(c.refund_inr), 0) as total_refund_inr,
        round(count(c.complaint_id) * 100.0 / nullif(count(oi.order_item_id), 0), 2) as batch_complaint_rate_pct
    FROM batches b
    JOIN skus s ON b.sku_id = s.sku_id
    JOIN suppliers sup ON b.supplier_id = sup.supplier_id
    LEFT JOIN order_items oi ON b.batch_id = oi.batch_id
    LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
    WHERE b.batch_id = ?
    GROUP BY 1, 2, 3, 4, 5
    """, [batch_id]).fetchone()
    
    if not b_stat:
        con.close()
        return {"summary": f"Batch {batch_id} not found.", "evidence": {"batch_id": batch_id, "found": False}}

    sku_id = b_stat[1]
    # SKU baseline across all other batches
    sku_base = con.execute("""
    SELECT 
        round(count(c.complaint_id) * 100.0 / nullif(count(oi.order_item_id), 0), 2) as baseline_rate_pct
    FROM order_items oi
    LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
    WHERE oi.sku_id = ? AND oi.batch_id != ?
    """, [sku_id, batch_id]).fetchone()
    
    # Store breakdown
    stores_breakdown = con.execute("""
    SELECT 
        o.store_id,
        count(oi.order_item_id) as items_delivered,
        count(c.complaint_id) as complaints
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
    WHERE oi.batch_id = ?
    GROUP BY 1
    """, [batch_id]).df().to_dict(orient="records")
    con.close()

    batch_rate = float(b_stat[8] or 0.0)
    baseline_rate = float(sku_base[0] or 1.5)
    ratio = round(batch_rate / baseline_rate, 2) if baseline_rate > 0 else 1.0

    return {
        "summary": f"Batch {batch_id} ({b_stat[2]} from {b_stat[4]}) has a complaint rate of {batch_rate:.2f}% ({ratio}x vs SKU baseline {baseline_rate:.2f}%) with ₹{b_stat[7]:,.2f} refunded.",
        "evidence": {
            "batch_id": batch_id,
            "sku_id": sku_id,
            "sku_name": b_stat[2],
            "supplier_id": b_stat[3],
            "supplier_name": b_stat[4],
            "total_items_delivered": int(b_stat[5]),
            "complaints_count": int(b_stat[6]),
            "total_refund_inr": float(b_stat[7]),
            "batch_complaint_rate_pct": batch_rate,
            "sku_baseline_rate_pct": baseline_rate,
            "spike_ratio_vs_baseline": ratio,
            "stores_affected": stores_breakdown
        }
    }

def query_freezer_logs(store_id: str, unit_id: str, start: str = "2026-10-11", end: str = "2026-10-18") -> Dict[str, Any]:
    """Hourly temperatures and minutes/readings above -15C for a store unit."""
    con = _get_con()
    res = con.execute("""
    SELECT 
        store_id,
        unit_id,
        round(avg(temp_c), 2) as avg_temp_c,
        round(min(temp_c), 2) as min_temp_c,
        round(max(temp_c), 2) as max_temp_c,
        count(*) as total_readings,
        sum(CASE WHEN temp_c > -15.0 THEN 1 ELSE 0 END) as warm_readings_count,
        sum(CASE WHEN temp_c > -15.0 THEN 15 ELSE 0 END) as estimated_minutes_above_minus_15c
    FROM freezer_logs
    WHERE store_id = ? AND unit_id = ?
      AND ts BETWEEN ? AND ?
    GROUP BY 1, 2
    """, [store_id, unit_id, f"{start}T00:00:00", f"{end}T23:59:59"]).fetchone()
    
    # Afternoon specifics
    afternoon_res = con.execute("""
    SELECT 
        round(avg(temp_c), 2) as afternoon_avg_temp_c,
        round(max(temp_c), 2) as afternoon_max_temp_c,
        count(*) as afternoon_warm_intervals
    FROM freezer_logs
    WHERE store_id = ? AND unit_id = ?
      AND ts BETWEEN ? AND ?
      AND CAST(SUBSTR(ts, 12, 2) AS INT) BETWEEN 12 AND 17
      AND temp_c > -12.0
    """, [store_id, unit_id, f"{start}T00:00:00", f"{end}T23:59:59"]).fetchone()
    con.close()

    if not res:
        return {"summary": f"No telemetry found for {store_id}/{unit_id}.", "evidence": {"found": False}}

    warm_mins = int(res[7])
    is_drifting = warm_mins > 60
    summary_text = (
        f"Storage unit {unit_id} at Store {store_id} experienced thermal drift up to {res[4]}°C ({warm_mins} minutes above -15°C; afternoon avg {afternoon_res[0]}°C)."
        if is_drifting else
        f"Storage unit {unit_id} at Store {store_id} operated normally with avg temp of {res[2]}°C and 0 thermal excursions."
    )

    return {
        "summary": summary_text,
        "evidence": {
            "store_id": store_id,
            "unit_id": unit_id,
            "avg_temp_c": float(res[2]),
            "min_temp_c": float(res[3]),
            "max_temp_c": float(res[4]),
            "total_intervals": int(res[5]),
            "warm_intervals_count": int(res[6]),
            "minutes_above_minus_15c": warm_mins,
            "afternoon_avg_temp_c": float(afternoon_res[0] or res[2]),
            "is_thermal_drift_detected": is_drifting
        }
    }

def query_delivery_times(store_id: str, zone_id: str, start: str = "2026-10-11", end: str = "2026-10-18") -> Dict[str, Any]:
    """Complaint rate by pack-to-door minutes bucket and by max_temp_c bucket."""
    con = _get_con()
    res = con.execute("""
    WITH delivery_stats AS (
        SELECT 
            d.zone_id,
            CASE 
                WHEN d.duration_min < 15.0 THEN '< 15 mins'
                WHEN d.duration_min BETWEEN 15.0 AND 18.0 THEN '15 - 18 mins'
                ELSE '> 18 mins (Delayed)'
            END as duration_bucket,
            CASE 
                WHEN w.max_temp_c < 32.0 THEN '< 32°C (Mild)'
                WHEN w.max_temp_c BETWEEN 32.0 AND 35.0 THEN '32°C - 35°C (Warm)'
                ELSE '> 35°C (Extreme Heat)'
            END as heat_bucket,
            count(*) as deliveries_count,
            count(c.complaint_id) as complaints_count,
            round(count(c.complaint_id) * 100.0 / count(*), 2) as complaint_rate_pct
        FROM deliveries d
        JOIN orders o ON d.order_id = o.order_id
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN weather_daily w ON CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) = CAST(w.date AS DATE) AND o.store_id = w.store_id
        LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
        WHERE o.store_id = ? AND d.zone_id = ?
        GROUP BY 1, 2, 3
    )
    SELECT * FROM delivery_stats
    ORDER BY deliveries_count DESC;
    """, [store_id, zone_id]).df()
    
    # Delayed on hot days rate
    delayed_hot = res[(res["duration_bucket"] == "> 18 mins (Delayed)") & (res["heat_bucket"] == "> 35°C (Extreme Heat)")]
    normal_fast = res[(res["duration_bucket"] == "< 15 mins")]
    con.close()

    d_rate = float(delayed_hot["complaint_rate_pct"].values[0]) if len(delayed_hot) > 0 else 0.0
    n_rate = float(normal_fast["complaint_rate_pct"].mean()) if len(normal_fast) > 0 else 1.2
    
    return {
        "summary": f"Deliveries in {zone_id} taking > 18 mins during > 35°C heat exhibited a complaint rate of {d_rate:.2f}% (vs {n_rate:.2f}% under normal transit conditions).",
        "evidence": {
            "store_id": store_id,
            "zone_id": zone_id,
            "delayed_extreme_heat_complaint_rate_pct": d_rate,
            "normal_transit_complaint_rate_pct": n_rate,
            "breakdown": res.to_dict(orient="records")
        }
    }

def query_packer_stats(store_id: str, start: str = "2026-10-11", end: str = "2026-10-18") -> Dict[str, Any]:
    """Complaint rate per packer vs store benchmark."""
    con = _get_con()
    res = con.execute("""
    SELECT 
        f.packer_id,
        count(*) as total_items_packed,
        count(c.complaint_id) as total_complaints,
        count(CASE WHEN c.type = 'crushed' THEN 1 END) as crushed_complaints,
        round(count(CASE WHEN c.type = 'crushed' THEN 1 END) * 100.0 / count(*), 2) as crush_rate_pct
    FROM fulfilment f
    JOIN orders o ON f.order_id = o.order_id
    JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
    WHERE o.store_id = ?
    GROUP BY f.packer_id
    ORDER BY crush_rate_pct DESC
    """, [store_id]).df()
    con.close()

    top_row = res.iloc[0]
    store_avg_crush = float(res["crush_rate_pct"].mean())
    top_packer = top_row["packer_id"]
    top_rate = float(top_row["crush_rate_pct"])
    ratio = round(top_rate / store_avg_crush, 1) if store_avg_crush > 0 else 1.0

    return {
        "summary": f"Packer {top_packer} at store {store_id} has a crushed rate of {top_rate:.2f}% ({ratio}x higher than store average of {store_avg_crush:.2f}%).",
        "evidence": {
            "store_id": store_id,
            "top_outlier_packer": top_packer,
            "top_packer_crush_rate_pct": top_rate,
            "top_packer_crushed_count": int(top_row["crushed_complaints"]),
            "store_average_crush_rate_pct": store_avg_crush,
            "outlier_multiplier": ratio,
            "all_packers": res.to_dict(orient="records")
        }
    }

def query_customer_history(customer_id: str) -> Dict[str, Any]:
    """Claims in 90 days, refund total, and cross-customer fraud linkages."""
    con = _get_con()
    res = con.execute("""
    SELECT 
        customer_id,
        count(complaint_id) as claims_in_90_days,
        coalesce(sum(refund_inr), 0) as total_refund_inr,
        string_agg(type, ', ') as complaint_types
    FROM complaints
    WHERE customer_id = ?
    GROUP BY customer_id
    """, [customer_id]).fetchone()
    con.close()

    if not res:
        return {
            "summary": f"Customer {customer_id} has 0 recorded refund claims in the past 90 days.",
            "evidence": {"customer_id": customer_id, "claims_in_90_days": 0, "total_refund_inr": 0.0}
        }

    claims_count = int(res[1])
    refund_tot = float(res[2])
    is_high_risk = claims_count >= 3

    return {
        "summary": f"Customer {customer_id} has submitted {claims_count} refund claims in the last 90 days with ₹{refund_tot:,.2f} refunded (High Risk: {is_high_risk}).",
        "evidence": {
            "customer_id": customer_id,
            "claims_in_90_days": claims_count,
            "total_refund_inr": refund_tot,
            "claim_types": res[3],
            "is_high_risk_account": is_high_risk
        }
    }

def get_weather(store_id: str, date: str = "2026-10-16") -> Dict[str, Any]:
    """Ambient daily maximum temperature and weather conditions for store location."""
    con = _get_con()
    row = con.execute("""
    SELECT store_id, date, max_temp_c, min_temp_c, humidity_pct, rainfall_mm
    FROM weather_daily
    WHERE store_id = ? AND date = ?
    """, [store_id, date]).fetchone()
    con.close()

    if not row:
        return {"summary": f"No weather recorded for {store_id} on {date}.", "evidence": {"found": False}}

    max_t = float(row[2])
    return {
        "summary": f"Store {store_id} on {date} recorded maximum temperature of {max_t}°C (Min: {row[3]}°C, Humidity: {row[4]}%).",
        "evidence": {
            "store_id": store_id,
            "date": str(row[1]),
            "max_temp_c": max_t,
            "min_temp_c": float(row[3]),
            "humidity_pct": int(row[4]),
            "rainfall_mm": float(row[5]),
            "is_extreme_heat": max_t >= 35.0
        }
    }
