-- ==============================================================================
-- Return Detective — BigQuery Evidence Views & Daily Analytical Rates
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. VIEW: v_freezer_hourly
-- Question it answers:
-- "What was the hourly min, avg, and max temperature for each storage unit/freezer
-- in each dark store, allowing us to pinpoint thermal drift windows?"
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW return_detective.v_freezer_hourly AS
SELECT
    store_id,
    unit_id,
    CAST(SUBSTR(ts, 1, 10) AS DATE) AS log_date,
    CAST(SUBSTR(ts, 12, 2) AS INT64) AS log_hour,
    ROUND(MIN(temp_c), 2) AS min_temp_c,
    ROUND(AVG(temp_c), 2) AS avg_temp_c,
    ROUND(MAX(temp_c), 2) AS max_temp_c,
    COUNT(*) AS reading_count,
    COUNTIF(temp_c > -12.0) AS warm_excursions
FROM return_detective.freezer_logs
GROUP BY 1, 2, 3, 4;


-- ------------------------------------------------------------------------------
-- 2. VIEW: v_complaint_chain
-- Question it answers:
-- "What is the complete forensic chain for every refund complaint: order -> SKU ->
-- batch -> supplier -> storage unit -> picker -> packer -> packing material ->
-- rider -> transit duration -> ambient temperature -> store freezer temp before dispatch?"
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW return_detective.v_complaint_chain AS
WITH freezer_2h_pre_pack AS (
    SELECT
        f.order_id,
        ROUND(AVG(fl.temp_c), 2) AS freezer_avg_temp_2h_before_pack
    FROM return_detective.fulfilment f
    JOIN return_detective.orders o ON f.order_id = o.order_id
    JOIN return_detective.order_items oi ON o.order_id = oi.order_id
    JOIN return_detective.batches b ON oi.batch_id = b.batch_id
    JOIN return_detective.freezer_logs fl ON fl.store_id = o.store_id
        AND fl.unit_id = b.storage_unit
        AND fl.ts BETWEEN SUBSTR(f.packed_at, 1, 19) AND SUBSTR(f.packed_at, 1, 19)
    GROUP BY f.order_id
)
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
    COALESCE(fp.freezer_avg_temp_2h_before_pack, -19.0) AS freezer_avg_temp_2h_before_pack

FROM return_detective.complaints c
JOIN return_detective.order_items oi ON c.order_item_id = oi.order_item_id
JOIN return_detective.orders o ON oi.order_id = o.order_id
JOIN return_detective.stores st ON o.store_id = st.store_id
JOIN return_detective.skus s ON oi.sku_id = s.sku_id
JOIN return_detective.batches b ON oi.batch_id = b.batch_id
JOIN return_detective.suppliers sup ON b.supplier_id = sup.supplier_id
JOIN return_detective.fulfilment f ON o.order_id = f.order_id
JOIN return_detective.deliveries d ON o.order_id = d.order_id
JOIN return_detective.zones zn ON d.zone_id = zn.zone_id
LEFT JOIN return_detective.weather_daily w ON CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) = CAST(w.date AS DATE) AND o.store_id = w.store_id
LEFT JOIN freezer_2h_pre_pack fp ON o.order_id = fp.order_id;


-- ------------------------------------------------------------------------------
-- 3. TABLE: daily_rates
-- Question it answers:
-- "What is the daily complaint rate per 1,000 order items across key operational slices:
-- (store x sku, store x batch, store x zone x hour, store x packer, and batch citywide)?
-- Used directly by BigQuery ML ARIMA_PLUS and z-score anomaly detectors."
-- ------------------------------------------------------------------------------
CREATE OR REPLACE TABLE return_detective.daily_rates AS

-- Slice 1: store x sku
WITH s_sku AS (
    SELECT
        CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) AS metric_date,
        'store_x_sku' AS slice_type,
        CONCAT(o.store_id, '::', oi.sku_id) AS slice_key,
        o.store_id,
        COUNT(DISTINCT oi.order_item_id) AS total_items,
        COUNT(DISTINCT c.complaint_id) AS complaint_count,
        COALESCE(SUM(c.refund_inr), 0) AS total_refund_inr
    FROM return_detective.orders o
    JOIN return_detective.order_items oi ON o.order_id = oi.order_id
    LEFT JOIN return_detective.complaints c ON oi.order_item_id = c.order_item_id
    GROUP BY 1, 2, 3, 4
),

-- Slice 2: store x batch
s_batch AS (
    SELECT
        CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) AS metric_date,
        'store_x_batch' AS slice_type,
        CONCAT(o.store_id, '::', oi.batch_id) AS slice_key,
        o.store_id,
        COUNT(DISTINCT oi.order_item_id) AS total_items,
        COUNT(DISTINCT c.complaint_id) AS complaint_count,
        COALESCE(SUM(c.refund_inr), 0) AS total_refund_inr
    FROM return_detective.orders o
    JOIN return_detective.order_items oi ON o.order_id = oi.order_id
    LEFT JOIN return_detective.complaints c ON oi.order_item_id = c.order_item_id
    GROUP BY 1, 2, 3, 4
),

-- Slice 3: store x zone x hour_bucket
s_zone_hr AS (
    SELECT
        CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) AS metric_date,
        'store_x_zone_x_hour' AS slice_type,
        CONCAT(o.store_id, '::', d.zone_id, '::H', SUBSTR(o.ordered_at, 12, 2)) AS slice_key,
        o.store_id,
        COUNT(DISTINCT oi.order_item_id) AS total_items,
        COUNT(DISTINCT c.complaint_id) AS complaint_count,
        COALESCE(SUM(c.refund_inr), 0) AS total_refund_inr
    FROM return_detective.orders o
    JOIN return_detective.order_items oi ON o.order_id = oi.order_id
    JOIN return_detective.deliveries d ON o.order_id = d.order_id
    LEFT JOIN return_detective.complaints c ON oi.order_item_id = c.order_item_id
    GROUP BY 1, 2, 3, 4
),

-- Slice 4: store x packer
s_packer AS (
    SELECT
        CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) AS metric_date,
        'store_x_packer' AS slice_type,
        CONCAT(o.store_id, '::', f.packer_id) AS slice_key,
        o.store_id,
        COUNT(DISTINCT oi.order_item_id) AS total_items,
        COUNT(DISTINCT c.complaint_id) AS complaint_count,
        COALESCE(SUM(c.refund_inr), 0) AS total_refund_inr
    FROM return_detective.orders o
    JOIN return_detective.order_items oi ON o.order_id = oi.order_id
    JOIN return_detective.fulfilment f ON o.order_id = f.order_id
    LEFT JOIN return_detective.complaints c ON oi.order_item_id = c.order_item_id
    GROUP BY 1, 2, 3, 4
),

-- Slice 5: batch (all stores)
batch_all AS (
    SELECT
        CAST(SUBSTR(o.ordered_at, 1, 10) AS DATE) AS metric_date,
        'batch_all_stores' AS slice_type,
        CONCAT('ALL::', oi.batch_id) AS slice_key,
        'ALL' AS store_id,
        COUNT(DISTINCT oi.order_item_id) AS total_items,
        COUNT(DISTINCT c.complaint_id) AS complaint_count,
        COALESCE(SUM(c.refund_inr), 0) AS total_refund_inr
    FROM return_detective.orders o
    JOIN return_detective.order_items oi ON o.order_id = oi.order_id
    LEFT JOIN return_detective.complaints c ON oi.order_item_id = c.order_item_id
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
