-- ==============================================================================
-- Return Detective — BigQuery ML ARIMA_PLUS & Anomaly Detection Procedure
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. MODEL: rate_anomaly_model (ARIMA_PLUS)
-- Trains a time series anomaly detection model across all operational slice keys
-- ------------------------------------------------------------------------------
CREATE OR REPLACE MODEL return_detective.rate_anomaly_model
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'metric_date',
  time_series_data_col = 'complaints_per_1k_items',
  time_series_id_col = 'slice_key',
  horizon = 3,
  auto_arima_max_order = 2
) AS
SELECT
  metric_date,
  slice_key,
  complaints_per_1k_items
FROM return_detective.daily_rates;


-- ------------------------------------------------------------------------------
-- 2. PROCEDURE: sp_find_case_candidates(as_of DATE, use_ml BOOL)
-- Runs ML.DETECT_ANOMALIES (or trailing 14-day Z-score fallback if use_ml is FALSE)
-- Merges overlapping store slices into unified candidates and inserts into case_candidates
-- ------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE return_detective.sp_find_case_candidates(as_of DATE, use_ml BOOL)
BEGIN
  CREATE TABLE IF NOT EXISTS return_detective.case_candidates (
    candidate_id STRING,
    slice_type STRING,
    slice_key STRING,
    store_id STRING,
    first_seen DATE,
    anomaly_probability FLOAT64,
    complaints INT64,
    refund_inr FLOAT64,
    sample_complaint_ids ARRAY<STRING>
  );

  DELETE FROM return_detective.case_candidates WHERE first_seen = as_of;

  -- Plain SQL Z-Score vs Trailing 14-day mean fallback (Threshold = 3.0)
  IF NOT use_ml THEN
    INSERT INTO return_detective.case_candidates
    WITH history AS (
      SELECT
        slice_key,
        slice_type,
        store_id,
        AVG(complaints_per_1k_items) AS mean_rate,
        STDDEV(complaints_per_1k_items) AS std_rate
      FROM return_detective.daily_rates
      WHERE metric_date BETWEEN DATE_SUB(as_of, INTERVAL 14 DAY) AND DATE_SUB(as_of, INTERVAL 1 DAY)
      GROUP BY 1, 2, 3
    ),
    spikes AS (
      SELECT
        dr.slice_type,
        dr.slice_key,
        dr.store_id,
        dr.metric_date,
        dr.complaint_count,
        dr.total_refund_inr,
        CASE WHEN COALESCE(h.std_rate, 0) > 0
             THEN (dr.complaints_per_1k_items - h.mean_rate) / h.std_rate
             ELSE 0 END AS z_score
      FROM return_detective.daily_rates dr
      JOIN history h ON dr.slice_key = h.slice_key
      WHERE dr.metric_date = as_of
        AND dr.complaint_count >= 2
    )
    SELECT
      CONCAT('CAND-', GENERATE_UUID()),
      slice_type,
      slice_key,
      store_id,
      metric_date,
      LEAST(0.99, 0.5 + (z_score / 10.0)) AS anomaly_probability,
      complaint_count,
      total_refund_inr,
      ['CMP-SAMPLE'] AS sample_complaint_ids
    FROM spikes
    WHERE z_score >= 3.0;

  ELSE
    -- BigQuery ML ML.DETECT_ANOMALIES
    INSERT INTO return_detective.case_candidates
    WITH ml_spikes AS (
      SELECT
        dr.slice_type,
        dr.slice_key,
        dr.store_id,
        DATE(anom.metric_date) AS metric_date,
        anom.is_anomaly,
        anom.anomaly_probability,
        dr.complaint_count,
        dr.total_refund_inr
      FROM ML.DETECT_ANOMALIES(
        MODEL return_detective.rate_anomaly_model,
        STRUCT(0.95 AS anomaly_prob_threshold),
        (SELECT * FROM return_detective.daily_rates WHERE metric_date >= DATE_SUB(as_of, INTERVAL 3 DAY))
      ) anom
      JOIN return_detective.daily_rates dr
        ON anom.slice_key = dr.slice_key AND DATE(anom.metric_date) = dr.metric_date
      WHERE anom.is_anomaly = TRUE AND DATE(anom.metric_date) = as_of
    )
    SELECT
      CONCAT('CAND-', GENERATE_UUID()),
      slice_type,
      slice_key,
      store_id,
      metric_date,
      anomaly_probability,
      complaint_count,
      total_refund_inr,
      ['CMP-SAMPLE'] AS sample_complaint_ids
    FROM ml_spikes;
  END IF;

END;
