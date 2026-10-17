#!/usr/bin/env bash
# ==============================================================================
# Return Detective — SQL Views & Tables Runner
# Applies views and tables in order to BigQuery (cloud) and DuckDB (local)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${REPO_ROOT}/.env" ]; then
  set -a
  source "${REPO_ROOT}/.env"
  set +a
fi

PROJECT_ID="${PROJECT_ID:-}"
DATASET="${BIGQUERY_DATASET:-return_detective}"

echo "=========================================================="
echo "📊 Compiling Return Detective Evidence Views & Rates"
echo "=========================================================="

# 1. Always build and sync local DuckDB views first
echo "Step 1: Building views in local DuckDB analytics database..."
python -m sql.build_views_duckdb

# 2. Run Sanity Checks locally
echo "Step 2: Executing 3 sanity verification queries..."
python -m sql.sanity_check

# 3. If BigQuery / GCP is configured, execute on BigQuery
if command -v bq &> /dev/null && [ -n "${PROJECT_ID}" ] && [ "${PROJECT_ID}" != "your-gcp-project-id" ]; then
  echo ""
  echo "Step 3: Deploying views and tables to BigQuery project ${PROJECT_ID}..."
  bq query --use_legacy_sql=false < "${SCRIPT_DIR}/views.sql"
  echo "✓ BigQuery views and tables deployed."
else
  echo ""
  echo "ℹ️  Cloud BigQuery skipped (PROJECT_ID not set or bq CLI not in PATH)."
  echo "   DuckDB analytical database is active and ready for all agent queries."
fi

echo "=========================================================="
echo "✅ Step 4 SQL views & rates compilation complete!"
echo "=========================================================="
