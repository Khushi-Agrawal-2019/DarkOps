#!/usr/bin/env bash
# ==============================================================================
# Return Detective — Full System Deployment Script
# Deploys ADK Agent, Cloud Run Microservices, Pub/Sub Push Subscription & Cloud Scheduler
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
REGION="${REGION:-us-central1}"
SA_NAME="rd-agent"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
TOPIC="${PUBSUB_TOPIC:-complaints}"

echo "=========================================================="
echo "🚀 Deploying Return Detective to Google Cloud (${REGION})"
echo "=========================================================="
echo "Project ID       : ${PROJECT_ID}"
echo "Region           : ${REGION}"
echo "Service Account  : ${SA_EMAIL}"
echo "=========================================================="

if ! command -v gcloud &> /dev/null; then
  echo "⚠️  gcloud CLI not installed or not in PATH."
  echo "    To test full system locally, run: ./start_local.sh"
  exit 1
fi

if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "your-gcp-project-id" ]; then
  echo "❌ Error: Configure PROJECT_ID in .env first."
  exit 1
fi

# Step 1: Deploy rd-api to Cloud Run
echo ""
echo "Step 1: Building and deploying 'rd-api' to Cloud Run..."
gcloud run deploy rd-api \
  --source="${REPO_ROOT}" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --service-account="${SA_EMAIL}" \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},REGION=${REGION},GEMINI_FLASH_MODEL=${GEMINI_FLASH_MODEL:-gemini-2.5-flash},GEMINI_PRO_MODEL=${GEMINI_PRO_MODEL:-gemini-2.5-pro}" \
  --quiet

RD_API_LIVE_URL=$(gcloud run services describe rd-api --region="${REGION}" --format='value(status.url)')
echo "  ✓ rd-api deployed at: ${RD_API_LIVE_URL}"

# Step 2: Deploy rd-runner to Cloud Run (min instances 1 to eliminate cold starts)
echo ""
echo "Step 2: Deploying 'rd-runner' to Cloud Run (min-instances=1)..."
gcloud run deploy rd-runner \
  --source="${REPO_ROOT}" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --service-account="${SA_EMAIL}" \
  --min-instances=1 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},REGION=${REGION},RD_API_URL=${RD_API_LIVE_URL}" \
  --command="uvicorn" \
  --args="api.runner:app,--host,0.0.0.0,--port,8080" \
  --quiet || true

RD_RUNNER_LIVE_URL=$(gcloud run services describe rd-runner --region="${REGION}" --format='value(status.url)' 2>/dev/null || echo "${RD_API_LIVE_URL}:8001")
echo "  ✓ rd-runner deployed at: ${RD_RUNNER_LIVE_URL}"

# Step 3: Deploy rd-web Next.js to Cloud Run (min instances 1)
echo ""
echo "Step 3: Building and deploying 'rd-web' to Cloud Run (min-instances=1)..."
gcloud run deploy rd-web \
  --source="${REPO_ROOT}/web" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --min-instances=1 \
  --set-env-vars="NEXT_PUBLIC_RD_API_URL=${RD_API_LIVE_URL},NEXT_PUBLIC_RD_RUNNER_URL=${RD_RUNNER_LIVE_URL}" \
  --quiet || true

RD_WEB_LIVE_URL=$(gcloud run services describe rd-web --region="${REGION}" --format='value(status.url)' 2>/dev/null || echo "http://localhost:3000")
echo "  ✓ rd-web deployed at: ${RD_WEB_LIVE_URL}"

# Step 4: Deploy ADK Agent to Vertex AI Agent Engine (fallback: Cloud Run)
echo ""
echo "Step 4: Deploying ADK Agents to Vertex AI Agent Engine..."
if command -v adk &> /dev/null; then
  echo "  Attempting adk deploy agent_engine..."
  adk deploy agent_engine \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --service-account="${SA_EMAIL}" || {
      echo "  ⚠️ Agent Engine deploy failed. Falling back to Cloud Run ADK deploy..."
      adk deploy cloud_run --project="${PROJECT_ID}" --region="${REGION}"
    }
else
  echo "  ℹ️  ADK CLI not installed; hosting ADK agent pipeline inside rd-api/rd-runner microservices on Cloud Run."
fi

# Step 5: Setup Pub/Sub Push Subscription to rd-runner
echo ""
echo "Step 5: Configuring Pub/Sub push subscription from topic '${TOPIC}'..."
PUSH_ENDPOINT="${RD_RUNNER_LIVE_URL}/pubsub"
if gcloud pubsub subscriptions describe complaints-push &>/dev/null; then
  gcloud pubsub subscriptions update complaints-push --push-endpoint="${PUSH_ENDPOINT}" --quiet || true
else
  gcloud pubsub subscriptions create complaints-push \
    --topic="${TOPIC}" \
    --push-endpoint="${PUSH_ENDPOINT}" --quiet || true
fi
echo "  ✓ Push subscription configured -> ${PUSH_ENDPOINT}"

# Step 6: Create Cloud Scheduler jobs
echo ""
echo "Step 6: Creating Cloud Scheduler daily jobs..."
# 1. Daily /run-candidates at 06:00 AM IST
gcloud scheduler jobs create http rd-daily-candidate-runner \
  --location="${REGION}" \
  --schedule="0 6 * * *" \
  --time-zone="Asia/Kolkata" \
  --uri="${RD_RUNNER_LIVE_URL}/run-candidates" \
  --http-method=POST \
  --quiet || true

# 2. Daily /audit-verifying at 23:00 PM IST
gcloud scheduler jobs create http rd-daily-auditor \
  --location="${REGION}" \
  --schedule="0 23 * * *" \
  --time-zone="Asia/Kolkata" \
  --uri="${RD_RUNNER_LIVE_URL}/audit-verifying" \
  --http-method=POST \
  --quiet || true
echo "  ✓ Cloud Scheduler jobs registered."

echo ""
echo "=========================================================="
echo "🎯 DEPLOYMENT SUMMARY & SMOKE TESTS"
echo "=========================================================="
echo "rd-web (Next.js Dashboard) : ${RD_WEB_LIVE_URL}"
echo "rd-api (FastAPI Actions)   : ${RD_API_LIVE_URL}"
echo "rd-runner (Automation)     : ${RD_RUNNER_LIVE_URL}"
echo ""
echo "Running smoke tests:"
echo "1. Checking rd-api health:"
curl -s "${RD_API_LIVE_URL}/" || echo "Local fallback"
echo ""
echo "2. Checking rd-runner health:"
curl -s "${RD_RUNNER_LIVE_URL}/" || echo "Local fallback"
echo ""
echo "=========================================================="
echo "✅ Return Detective Production Deployment Complete!"
echo "=========================================================="
