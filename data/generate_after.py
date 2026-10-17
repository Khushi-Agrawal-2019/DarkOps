"""
Return Detective — Post-Intervention (+7 Days) Data Generator
Simulates the 7 days following agent actions:
  - Batch B-4471 quarantined; fresh Batch B-4472 received with 1.2% normal rot
  - S1 Freezer F2 repaired by HVAC ticket; afternoon temp stays at -19.2°C
  - S2 Zone 3 thermal routing enforced; delivery transit < 12 mins, melts drop to 0
  - S3 Packer PK-308 retrained with protective cushion; crushed eggs drop to baseline (1%)
"""

import os
import datetime
from datetime import timedelta
import random
import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "out", "return_detective.duckdb")
ANCHOR_DATE = datetime.datetime(2026, 10, 18, 23, 59, 59)

def generate_7_days_after():
    print("⏩ Simulating +7 Days of Post-Intervention Operational Data...")
    con = duckdb.connect(DB_PATH)
    
    # 7 days forward: 2026-10-19 to 2026-10-25
    after_days = 7
    new_orders = []
    new_order_items = []
    new_fulfilment = []
    new_deliveries = []
    new_complaints = []
    new_freezer_logs = []
    
    order_id_counter = 200000
    item_id_counter = 700000
    complaint_id_counter = 900000
    
    # Replacement batch for Tomatoes
    con.execute("""
    INSERT INTO batches VALUES 
    ('B-4472', 'SKU-001', 'SUP-007', '2026-10-19T06:00:00', '2026-10-26T00:00:00', 'ambient-01');
    """)

    for d_idx in range(1, after_days + 1):
        day_date = ANCHOR_DATE + timedelta(days=d_idx)
        daily_orders = random.randint(580, 680)
        
        for _ in range(daily_orders):
            order_id_counter += 1
            oid = f"ORD-AFTER-{order_id_counter}"
            s_id = random.choice(["S1", "S2", "S3", "S4"])
            o_hour = random.randint(8, 22)
            o_time = day_date.replace(hour=o_hour, minute=random.randint(0, 59))
            
            # Order items (clean baseline operations)
            item_id_counter += 1
            iid = f"ITEM-AFTER-{item_id_counter}"
            # Fresh produce / Tomatoes replaced with B-4472
            sku_id = random.choice(["SKU-001", "SKU-009", "SKU-011", "SKU-020"])
            b_id = "B-4472" if sku_id == "SKU-001" else "B-1005"
            
            new_orders.append({
                "order_id": oid,
                "store_id": s_id,
                "customer_id": f"CUST-{random.randint(1, 8000):05d}",
                "ordered_at": o_time.isoformat(),
                "total_inr": 240,
                "status": "delivered"
            })
            
            new_order_items.append({
                "order_item_id": iid,
                "order_id": oid,
                "sku_id": sku_id,
                "batch_id": b_id,
                "quantity": 1,
                "unit_price_inr": 65,
                "storage_req": "frozen" if sku_id == "SKU-009" else "ambient",
                "category": "dairy_frozen" if sku_id == "SKU-009" else "fresh_produce"
            })
            
            new_fulfilment.append({
                "order_id": oid,
                "picker_id": "PKR-002",
                "packer_id": "PK-308" if s_id == "S3" else "PK-301",
                "packing_material": "insulated_bubble" if sku_id == "SKU-009" else "cardboard_tray",
                "packed_at": (o_time + timedelta(minutes=4)).isoformat()
            })
            
            new_deliveries.append({
                "order_id": oid,
                "rider_id": "RD-012",
                "zone_id": f"{s_id}-Z3" if s_id == "S2" else f"{s_id}-Z1",
                "distance_km": 2.1,
                "packed_at": (o_time + timedelta(minutes=4)).isoformat(),
                "delivered_at": (o_time + timedelta(minutes=15)).isoformat(),
                "duration_min": 11.2 # Post-intervention routing keeps transit fast (<12 min)!
            })
            
            # Baseline normal complaints only (~0.5%)
            if random.random() < 0.005:
                complaint_id_counter += 1
                new_complaints.append({
                    "complaint_id": f"CMP-AFTER-{complaint_id_counter}",
                    "order_item_id": iid,
                    "customer_id": f"CUST-0001",
                    "type": "damaged_pack",
                    "text": "small tear on outer carry bag",
                    "photo_uri": None,
                    "refund_inr": 65.0,
                    "created_at": (o_time + timedelta(minutes=60)).isoformat(),
                    "gemini_verdict": None,
                    "gemini_severity": None,
                    "photo_embedding": None
                })

    # Freezer logs: S1 Freezer F2 is now fixed at -19.4°C afternoon
    cur_t = ANCHOR_DATE + timedelta(minutes=15)
    end_t = ANCHOR_DATE + timedelta(days=7)
    while cur_t <= end_t:
        for s in ["S1", "S2", "S3", "S4"]:
            for u in ["F1", "F2", "C1"]:
                temp = -19.4 + random.uniform(-0.4, 0.4) if u.startswith("F") else 3.2
                new_freezer_logs.append({
                    "store_id": s,
                    "unit_id": u,
                    "ts": cur_t.isoformat(),
                    "temp_c": round(temp, 1)
                })
        cur_t += timedelta(minutes=15)

    # Insert into DuckDB
    con.register("df_no", pd.DataFrame(new_orders))
    con.execute("INSERT INTO orders SELECT * FROM df_no")
    
    con.register("df_ni", pd.DataFrame(new_order_items))
    con.execute("INSERT INTO order_items SELECT * FROM df_ni")
    
    con.register("df_nf", pd.DataFrame(new_fulfilment))
    con.execute("INSERT INTO fulfilment SELECT * FROM df_nf")
    
    con.register("df_nd", pd.DataFrame(new_deliveries))
    con.execute("INSERT INTO deliveries SELECT * FROM df_nd")
    
    if new_complaints:
        con.register("df_nc", pd.DataFrame(new_complaints))
        con.execute("INSERT INTO complaints (complaint_id, order_item_id, customer_id, type, text, photo_uri, refund_inr, created_at) SELECT complaint_id, order_item_id, customer_id, type, text, photo_uri, refund_inr, created_at FROM df_nc")
        
    con.register("df_nfl", pd.DataFrame(new_freezer_logs))
    con.execute("INSERT INTO freezer_logs SELECT * FROM df_nfl")
    
    # Re-run daily_rates compilation
    from sql.build_views_duckdb import build_views
    build_views()
    con.close()
    print("✅ +7 Days Data Appended Successfully: Scenarios 1-4 resolved to baseline!")

if __name__ == "__main__":
    generate_7_days_after()
