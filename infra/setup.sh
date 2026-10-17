#!/usr/bin/env bash
# ==============================================================================
# Return Detective — Google Cloud Infrastructure Setup
# Idempotent provisioning of all GCP services, IAM roles, BigQuery, GCS, Firestore
# ==============================================================================

set -euo pipefail

# Find repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Load .env if present
if [ -f "${REPO_ROOT}/.env" ]; then
  # export variables from .env
  set -a
  source "${REPO_ROOT}/.env"
  set +a
fi

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
BIGQUERY_LOCATION="${BIGQUERY_LOCATION:-US}"
DATASET="${BIGQUERY_DATASET:-return_detective}"
BUCKET="${GCS_BUCKET:-${PROJECT_ID}-rd-photos}"
TOPIC="${PUBSUB_TOPIC:-complaints}"
SUB="${PUBSUB_SUBSCRIPTION:-complaints-sub}"
SA_NAME="rd-agent"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================================="
echo "🕵️  Return Detective — Google Cloud Infrastructure Setup"
echo "=========================================================="
echo "Project ID        : ${PROJECT_ID}"
echo "Region            : ${REGION}"
echo "BigQuery Location : ${BIGQUERY_LOCATION}"
echo "Dataset           : ${DATASET}"
echo "Storage Bucket    : gs://${BUCKET}"
echo "Pub/Sub Topic     : ${TOPIC}"
echo "Service Account   : ${SA_EMAIL}"
echo "=========================================================="

if ! command -v gcloud &> /dev/null; then
  echo "⚠️  gcloud CLI is not installed or not in PATH."
  echo "    Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
  echo "    Or test in local mode by setting MOCK_MODE=true in .env."
  exit 1
fi

if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "your-gcp-project-id" ]; then
  echo "❌ Error: PROJECT_ID is not configured in .env. Please set a valid GCP project ID."
  exit 1
fi

gcloud config set project "${PROJECT_ID}" --quiet

echo ""
echo "Step 1: Enabling required Google Cloud APIs..."
APIS=(
  aiplatform.googleapis.com
  bigquery.googleapis.com
  storage.googleapis.com
  firestore.googleapis.com
  pubsub.googleapis.com
  run.googleapis.com
  cloudbuild.googleapis.com
  artifactregistry.googleapis.com
  cloudscheduler.googleapis.com
  logging.googleapis.com
  cloudtrace.googleapis.com
  secretmanager.googleapis.com
)

for api in "${APIS[@]}"; do
  echo "  - Checking/enabling ${api}..."
  gcloud services enable "${api}" --quiet || true
done

echo ""
echo "Step 2: Provisioning Cloud Storage bucket gs://${BUCKET}..."
if gcloud storage buckets describe "gs://${BUCKET}" &>/dev/null; then
  echo "  ✓ Bucket gs://${BUCKET} already exists."
else
  echo "  + Creating bucket gs://${BUCKET} in ${REGION} with uniform bucket-level access..."
  gcloud storage buckets create "gs://${BUCKET}" \
    --location="${REGION}" \
    --uniform-bucket-level-access --quiet || true
fi

echo ""
echo "Step 3: Provisioning BigQuery dataset ${DATASET} in location ${BIGQUERY_LOCATION}..."
if bq show --dataset "${PROJECT_ID}:${DATASET}" &>/dev/null; then
  echo "  ✓ BigQuery dataset ${DATASET} already exists."
else
  echo "  + Creating BigQuery dataset ${DATASET}..."
  bq --location="${BIGQUERY_LOCATION}" mk --dataset --description "Return Detective hackathon analytics dataset" "${PROJECT_ID}:${DATASET}" || true
fi

echo ""
echo "Step 4: Ensuring Firestore in Native mode exists..."
if gcloud firestore databases describe --database="(default)" &>/dev/null; then
  echo "  ✓ Firestore database (default) exists."
else
  echo "  + Creating Firestore (default) database in ${REGION} (Native mode)..."
  gcloud firestore databases create --location="${REGION}" --type=firestore-native --quiet || true
fi

echo ""
echo "Step 5: Provisioning Pub/Sub topic '${TOPIC}' and subscription '${SUB}'..."
if gcloud pubsub topics describe "${TOPIC}" &>/dev/null; then
  echo "  ✓ Pub/Sub topic ${TOPIC} already exists."
else
  echo "  + Creating Pub/Sub topic ${TOPIC}..."
  gcloud pubsub topics create "${TOPIC}" --quiet || true
fi

if gcloud pubsub subscriptions describe "${SUB}" &>/dev/null; then
  echo "  ✓ Pub/Sub subscription ${SUB} already exists."
else
  echo "  + Creating pull subscription ${SUB} on topic ${TOPIC}..."
  gcloud pubsub subscriptions create "${SUB}" --topic="${TOPIC}" --quiet || true
fi

echo ""
echo "Step 6: Creating least-privilege Service Account '${SA_NAME}'..."
if gcloud iam service-accounts describe "${SA_EMAIL}" &>/dev/null; then
  echo "  ✓ Service account ${SA_EMAIL} already exists."
else
  echo "  + Creating service account ${SA_NAME}..."
  gcloud iam service-accounts create "${SA_NAME}" \
    --description="Least-privilege execution identity for Return Detective ADK agents" \
    --display-name="Return Detective Agent" --quiet || true
fi

echo "  Assigning specific IAM roles:"
# Explanations of each role:
# - roles/aiplatform.user: Call Gemini 2.5/1.5 & Imagen & Multimodal embeddings on Vertex AI
# - roles/bigquery.dataViewer: Read complaints, orders, freezer telemetry & analytical views
# - roles/bigquery.jobUser: Execute analytical queries & BQ ML anomaly detection
# - roles/datastore.user: Read/write cases, hypotheses, and action audit records in Firestore
# - roles/pubsub.publisher: Publish incoming complaint events
# - roles/run.invoker: Invoke internal mock store & runner microservices on Cloud Run
# - roles/storage.objectViewer: Read complaint photos from GCS bucket for forensics analysis

ROLES=(
  roles/aiplatform.user
  roles/bigquery.dataViewer
  roles/bigquery.jobUser
  roles/datastore.user
  roles/pubsub.publisher
  roles/run.invoker
  roles/storage.objectViewer
)

for role in "${ROLES[@]}"; do
  echo "    -> Binding ${role}..."
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${role}" \
    --condition=None --quiet >/dev/null || true
done

echo ""
echo "=========================================================="
echo "✅ Infrastructure Provisioning Complete!"
echo "=========================================================="
echo "GCS Bucket   : gs://${BUCKET}"
echo "BigQuery     : ${PROJECT_ID}:${DATASET} (${BIGQUERY_LOCATION})"
echo "Firestore    : (default) in ${REGION}"
echo "Pub/Sub      : topic=${TOPIC}, sub=${SUB}"
echo "Agent SA     : ${SA_EMAIL}"
echo "=========================================================="
