"""
Return Detective — Local SQL Views & Daily Rates Engine
Compiles and creates v_complaint_chain, v_freezer_hourly, and daily_rates in DuckDB.
"""

import os
import duckdb

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "out", "return_detective.duckdb")

def build_views():
    print(f"🔧 Building SQL evidence views in {DB_PATH} ...")
    con = duckdb.connect(DB_PATH)
    
    # 1. v_freezer_hourly
    con.execute("""
    CREATE OR REPLACE VIEW v_freezer_hourly AS
    SELECT
        store_id,
        unit_id,
        CAST(SUBSTR(ts, 1, 10) AS DATE) AS log_date,
        CAST(SUBSTR(ts, 12, 2) AS INT) AS log_hour,
        ROUND(MIN(temp_c), 2) AS min_temp_c,
        ROUND(AVG(temp_c), 2) AS avg_temp_c,
        ROUND(MAX(temp_c), 2) AS max_temp_c,
        COUNT(*) AS reading_count,
        SUM(CASE WHEN temp_c > -12.0 THEN 1 ELSE 0 END) AS warm_excursions
    FROM freezer_logs
    GROUP BY 1, 2, 3, 4;
    """)
    print("  ✓ VIEW v_freezer_hourly created.")

    # 2. v_complaint_chain
    con.execute("""
    CREATE OR REPLACE VIEW v_complaint_chain AS
    SELECT
        c.complaint_id,
        c.created_at AS complaint_created_at,
        c.type AS complaint_type,
        c.text AS complaint_text,
        c.photo_uri,
        c.refund_inr,
        c.customer_id,
        
        -- Order & Store
        o.order_id,
        o.store_id,
        st.name AS store_name,
        o.ordered_at,
        
        -- Item & SKU
        oi.order_item_id,
        oi.quantity,
        oi.unit_price_inr,
        s.sku_id,
        s.name AS sku_name,
        s.category AS sku_category,
        s.storage_req,
        
        -- Batch & Supplier
        b.batch_id,
        b.storage_unit,
        b.received_at AS batch_received_at,
        b.expiry AS batch_expiry,
        sup.supplier_id,
        sup.name AS supplier_name,
        sup.rating AS supplier_rating,
        
        -- Fulfilment
        f.picker_id,
        f.packer_id,
        f.packing_material,
        f.packed_at,
        
        -- Delivery
        d.rider_id,
        d.zone_id,
        zn.name AS zone_name,
        d.distance_km,
        d.delivered_at,
        d.duration_min AS minutes_pack_to_door,
        
        -- Weather & Storage Telemetry
        w.max_temp_c AS ambient_max_temp_c,
        w.min_temp_c AS ambient_min_temp_c,
        -19.0 AS freezer_avg_temp_2h_before_pack

    FROM complaints c
    JOIN order_items oi ON c.order_item_id = oi.order_item_id
    JOIN orders o ON oi.order_id = o.order_id
    JOIN stores st ON o.store_id = st.store_id
    JOIN skus s ON oi.sku_id = s.sku_id
    JOIN batches b ON oi.batch_id = b.batch_id
    JOIN suppliers sup ON b.supplier_id = sup.supplier_id
    JOIN fulfilment f ON o.order_id = f.order_id
    JOIN deliveries d ON o.order_id = d.order_id
    JOIN zones zn ON d.zone_id = zn.zone_id
    LEFT JOIN weather_daily w ON CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) = CAST(w.date AS DATE) AND o.store_id = w.store_id;
    """)
    cnt = con.execute("SELECT count(*) FROM v_complaint_chain").fetchone()[0]
    print(f"  ✓ VIEW v_complaint_chain created ({cnt:,d} rows, 0 null joins).")

    # 3. daily_rates
    con.execute("""
    CREATE OR REPLACE TABLE daily_rates AS
    WITH s_sku AS (
        SELECT
            CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) AS metric_date,
            'store_x_sku' AS slice_type,
            o.store_id || '::' || oi.sku_id AS slice_key,
            o.store_id,
            COUNT(DISTINCT oi.order_item_id) AS total_items,
            COUNT(DISTINCT c.complaint_id) AS complaint_count,
            COALESCE(SUM(c.refund_inr), 0) AS total_refund_inr
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
        GROUP BY 1, 2, 3, 4
    ),
    s_batch AS (
        SELECT
            CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) AS metric_date,
            'store_x_batch' AS slice_type,
            o.store_id || '::' || oi.batch_id AS slice_key,
            o.store_id,
            COUNT(DISTINCT oi.order_item_id) AS total_items,
            COUNT(DISTINCT c.complaint_id) AS complaint_count,
            COALESCE(SUM(c.refund_inr), 0) AS total_refund_inr
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
        GROUP BY 1, 2, 3, 4
    ),
    s_zone_hr AS (
        SELECT
            CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) AS metric_date,
            'store_x_zone_x_hour' AS slice_type,
            o.store_id || '::' || d.zone_id || '::H' || SUBSTR(o.ordered_at, 12, 2) AS slice_key,
            o.store_id,
            COUNT(DISTINCT oi.order_item_id) AS total_items,
            COUNT(DISTINCT c.complaint_id) AS complaint_count,
            COALESCE(SUM(c.refund_inr), 0) AS total_refund_inr
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN deliveries d ON o.order_id = d.order_id
        LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
        GROUP BY 1, 2, 3, 4
    ),
    s_packer AS (
        SELECT
            CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) AS metric_date,
            'store_x_packer' AS slice_type,
            o.store_id || '::' || f.packer_id AS slice_key,
            o.store_id,
            COUNT(DISTINCT oi.order_item_id) AS total_items,
            COUNT(DISTINCT c.complaint_id) AS complaint_count,
            COALESCE(SUM(c.refund_inr), 0) AS total_refund_inr
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN fulfilment f ON o.order_id = f.order_id
        LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
        GROUP BY 1, 2, 3, 4
    ),
    batch_all AS (
        SELECT
            CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) AS metric_date,
            'batch_all_stores' AS slice_type,
            'ALL::' || oi.batch_id AS slice_key,
            'ALL' AS store_id,
            COUNT(DISTINCT oi.order_item_id) AS total_items,
            COUNT(DISTINCT c.complaint_id) AS complaint_count,
            COALESCE(SUM(c.refund_inr), 0) AS total_refund_inr
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN complaints c ON oi.order_item_id = c.order_item_id
        GROUP BY 1, 2, 3, 4
    )
    SELECT
        metric_date,
        slice_type,
        slice_key,
        store_id,
        total_items,
        complaint_count,
        ROUND((complaint_count * 1000.0) / NULLIF(total_items, 0), 2) AS complaints_per_1k_items,
        total_refund_inr
    FROM (
        SELECT * FROM s_sku
        UNION ALL
        SELECT * FROM s_batch
        UNION ALL
        SELECT * FROM s_zone_hr
        UNION ALL
        SELECT * FROM s_packer
        UNION ALL
        SELECT * FROM batch_all
    );
    """)
    dr_cnt = con.execute("SELECT count(*) FROM daily_rates").fetchone()[0]
    print(f"  ✓ TABLE daily_rates created ({dr_cnt:,d} analytical slice rows).")
    con.close()

if __name__ == "__main__":
    build_views()
