# 🕵️ DarkOps — Autonomous Root-Cause Investigation for Quick-Commerce

> **AI Builder Cup 2026** · Google Cloud Hackathon Submission by Team **SherlOps**  
> *Autonomous multi-agent system that turns customer refund complaints into forensic supply-chain evidence, isolates root causes across 5 parallel hypotheses, executes guardrailed interventions, and audits resolution.*

---

## 📌 Problem Statement (Why This Matters)
Quick-commerce platforms (Blinkit, Zepto, Instamart) bleed millions of rupees each month by treating customer refund complaints as transactional customer-support costs rather than supply-chain telemetry. When perishable items spoil, milk packets tear, or ice cream melts, platforms issue automatic refunds to protect customer NPS while leaving underlying operational failures undetected. Because dark store operations span disparate silos—inbound supplier batches, warehouse refrigeration, human packers, and last-mile thermal transit—identifying the true root cause takes days of manual post-mortem, allowing bad inventory and equipment failures to continue bleeding revenue.

---

## 🔍 What DarkOps Does
DarkOps is an autonomous multi-agent operational detective for dark store networks.

1. **Multimodal Evidence Ingestion:** Ingests customer complaint text, timestamped fulfillment logs, IoT sensor readings, and complaint photos verified by **Gemini 2.5 Flash** with optical character recognition (OCR) and vector embeddings.
2. **Spike Detection & Clustering:** Monitors operational slices across dark stores using **BigQuery ML ARIMA_PLUS** anomaly detection to automatically open investigative case files when complaint clusters emerge.
3. **Parallel Hypothesis Investigation:** Deploys a panel of 5 specialized LLM sub-agents running in parallel on **Gemini 2.5 Pro**—testing storage refrigeration, supplier batch rot, last-mile transit duration, packer human error, and coordinated refund abuse rings.
4. **Deterministic Guardrailed Action:** Evaluates proposed remedies through strict deterministic policy tiers:
   - **Auto-tier** ($\ge 0.80$ confidence, fully reversible, impact $< ₹5,000$): Batch quarantine, proactive customer notifications, cooling unit maintenance tickets.
   - **Approve-tier** (High financial impact or irreversible): One-tap store manager approval via **Google Chat Cards v2** or web interface for supplier chargeback debit notes.
   - **Recommend-tier**: Strategic vendor renegotiations escalated to executive leadership.
5. **Closed-Loop Audit (+7 Days):** Re-evaluates dark store slice complaint metrics 7 days post-intervention. If complaint rates drop $\ge 60\%$, the case is permanently closed and quantified in net rupees prevented; if unresolved, it reopens and pivots to secondary hypotheses.

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph Ingestion ["1. Multimodal Evidence Ingestion"]
        A[Customer Complaint + Photo] --> B[Gemini 2.5 Flash Forensics]
        B -->|Defect Type, OCR, Severity| C[(BigQuery Complaint Chain)]
        B -->|512-dim Perceptual Vector| D[(BigQuery VECTOR_SEARCH)]
        IoT[Freezer IoT Logs] --> C
        OPS[Packer & Rider Logs] --> C
        MET[Weather / Ambient Temp] --> C
    end

    subgraph Detection ["2. Anomaly Clustering"]
        C --> E[BigQuery ML ARIMA_PLUS]
        E -->|Spike Probability >= 0.90| F[Case Candidate Generator]
        D -->|Cosine Similarity >= 0.95| G[Refund Abuse Ring Detector]
    end

    subgraph Coordination ["3. Autonomous Multi-Agent Panel"]
        F --> H[Chief Inspector Coordinator\nGemini 2.5 Pro]
        G --> H
        H --> I[Parallel Detective Panel]
        
        subgraph Hypotheses ["5 Parallel Hypothesis Testers"]
            I --> H1[Storage Refrigeration Tester]
            I --> H2[Supplier Batch Tester]
            I --> H3[Delivery Transit Tester]
            I --> H4[Packer Negligence Tester]
            I --> H5[Fraud Abuse Ring Tester]
        end

        H1 & H2 & H3 & H4 & H5 --> J[Ranker Agent\nCaseFinding Schema]
    end

    subgraph Execution ["4. Guardrailed Enforcement"]
        J --> K[Deterministic Policy Engine]
        K -->|Auto Tier| L[FastAPI Dark Store API]
        K -->|Approve Tier| M[Google Chat Cards v2 / Next.js Web]
        L --> N[(Firestore Case & Audit State)]
        M -->|1-Tap Approval| L
    end

    subgraph Audit ["5. Closed-Loop Verification"]
        N --> O[Auditor Agent]
        O -->|+7 Days Rate Comparison| P{Drop >= 60%?}
        P -->|Yes| Q[Case Closed: Rupees Prevented Quantified]
        P -->|No| R[Case Reopened: Pivot to Next Hypothesis]
    end
```

---

## ☁️ Google Cloud Products Used & Why

| Google Cloud Product | Purpose & Role in Return Detective | Why It Was Chosen |
| :--- | :--- | :--- |
| **Gemini 2.5 Pro** | Powers Chief Inspector coordinator and the 5 parallel hypothesis testing sub-agents. | Superior multi-step reasoning, complex structured output generation (`HypothesisResult`, `CaseFinding`), and high factual precision when balancing contradictory evidence. |
| **Gemini 2.5 Flash** | Multimodal forensic photo analysis, defect classification, OCR (batch/expiry dates), and Enforcer action generation. | Sub-second latency and cost efficiency for processing thousands of inbound complaint photos and generating operational audit summaries. |
| **BigQuery & BigQuery ML** | Analytical data warehouse hosting joined `v_complaint_chain`, `daily_rates` view slices, and ARIMA_PLUS anomaly detection. | Scales to millions of dark store transactions, joining 9 operational dimensions without latency and detecting non-trivial time-series spikes natively inside SQL. |
| **BigQuery VECTOR_SEARCH** | Perceptual visual embedding storage and cross-customer similarity search. | Performs sub-second cosine distance searches across photos to isolate fraud rings reusing identical or cropped pictures across multiple accounts. |
| **Cloud Run** | Serverless hosting for `rd-api` (store mock service), `rd-runner` (agent batch scheduler), and `rd-web` (Next.js dashboard). | Fully managed, instant auto-scaling with zero idle server cost, native Cloud Logging, and zero-cold-start options for judging. |
| **Firestore (Native Mode)** | Real-time operational database holding case records, action logs, audit trails, and live UI listeners. | Sub-millisecond read/writes with live websocket-style streaming (`onSnapshot`) so dashboard screens update in real time as agents execute steps. |
| **Cloud Storage (GCS)** | Object storage (`gs://$PROJECT_ID-rd-photos`) for high-resolution complaint photos and supplier claim evidence packs. | Secure, high-durability object storage with direct signed URLs for Google Chat Cards and Next.js frontends. |
| **Pub/Sub** | Asynchronous ingestion pipeline decoupled from dark store webhooks (`complaints` topic and pull/push subscriptions). | Guaranteed at-least-once delivery capable of buffering bursts during peak flash-sale hours (7–10 PM). |
| **Cloud Scheduler & Cloud Trace** | Automated daily candidate triggers, recurring 7-day post-intervention audits, and end-to-end distributed agent tracing. | Hands-off autonomous cron orchestration and distributed observability across multi-agent tool execution steps. |

---

## 🎯 The 6 Planted Real-World Scenarios

The system was evaluated against a 60-day synthetic dataset across 4 Bengaluru dark stores (S1 Koramangala, S2 Indiranagar, S3 HSR Layout, S4 Whitefield) containing 42,102 orders and 1,654 complaints:

| Scenario | Dark Stores | Root Cause | Planted Signal & Evidence | Autonomous Action Taken | +7 Days Audit Outcome |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Agricultural Spoilage** | S1, S2, S3 | `supplier_batch` | Tomato Batch `B-4471` (GreenLeaf Farms) has **6.0x baseline rot rate** across all 3 stores simultaneously. | **Auto:** Batch quarantined (0 sellable units).<br>**Approve:** ₹14,200 supplier debit claim card sent to store manager. | **Closed** (Rot dropped 83%, ₹48,600 prevented). |
| **2. Storage Drift** | S1 | `storage_temperature` | Freezer `F2` afternoon temperature drifts from -19°C to **-8°C for 2.5 hours**, melting ice-cream and frozen goods. | **Auto:** High-priority HVAC maintenance ticket dispatched; stock temporarily moved to cold room C1. | **Closed** (Melt complaints dropped 92%, ₹32,400 prevented). |
| **3. Delivery Heat Transit** | S2 | `delivery_transit` | Zone 3 transit durations **> 18 mins during > 35°C peak afternoon heat** causing ice cream melt; freezer F1 normal (-19°C). | **Auto:** Thermal routing cap updated (< 15 mins for heat-sensitive SKUs); proactive delivery alerts sent. | **Closed** (Melt complaints dropped 100%, ₹21,800 prevented). |
| **4. Human Packing Negligence** | S3 | `packing_negligence` | Store S3 Packer `PK-308` produces a crushed egg complaint rate **5.2x higher than store benchmark** (placing heavy cans atop egg cartons). | **Auto:** Packing workstation rule updated requiring cardboard trays and bubble wrap; mandatory retraining flag set. | **Closed** (Crush complaints dropped 88%, ₹18,900 prevented). |
| **5. Coordinated Refund Abuse Ring** | All Stores | `refund_abuse` | 3 distinct customer accounts (`CUST-ABUSE-101`, `102`, `103`) reusing **2 near-identical cropped photos** across 9 refund claims (cosine distance < 0.05). | **Auto:** Refund requests frozen across all 3 linked accounts; accounts flagged for store investigator review. | **Resolved** (₹3,780 in fraudulent refunds successfully prevented). |
| **6. Red Herring Spike** | Citywide | `inconclusive` | Single-day 24h citywide bakery complaint spike with diffuse root causes (no single batch, packer, rider, or temperature anomaly). | **Safe Inaction:** Confidence < 0.50. Case marked **"watching"**; zero disruptive operational changes initiated. | **Watching** (Normalized naturally; prevents wasteful false-alarm interventions). |

---

## ⚖️ What Is Mocked vs Real

| Component | Status | Implementation Details |
| :--- | :---: | :--- |
| **Multi-Agent Reasoning** | **REAL** | Built with Google GenAI SDK and ADK agent architectures (`LlmAgent`, `ParallelAgent`, `SequentialAgent`). Gemini 2.5 Pro and Flash models run actual prompts and structured schemas. |
| **Photo Forensics & OCR** | **REAL** | Real Gemini Flash multimodal vision inspecting uploaded complaint photos, performing OCR on batch numbers and expiry stamps, and rating defect severity. |
| **Vector Similarity Search** | **REAL** | 512-dimension perceptual feature vectors stored and searched via cosine distance to catch cropped photo reuse rings. |
| **SQL Views & Analytics** | **REAL** | DuckDB analytical engine locally (100% BigQuery SQL compliant) joining 9 operational dimensions across 42,000+ orders and 218,000 analytical slice rows. |
| **Web Dashboard** | **REAL** | Fully reactive Next.js 14 App Router with Tailwind CSS, live polling, 3-column forensic investigation interface, and Indian Rupee formatting. |
| **Approval Workflows** | **REAL** | Google Chat Cards v2 payload generation and interactive HTTP callback handling directly updating action status in real time. |
| **Dark Store Operational Data**| **SYNTHETIC** | High-fidelity synthetic dataset generated based on real-world Indian quick-commerce patterns (Blinkit/Zepto SKU pricing, peak hours 7-10 PM, Indian English complaint phrasing). |
| **WMS / ERP Execution** | **MOCKED VIA API** | Real FastAPI microservice (`rd-api`) mocking inventory quarantine, supplier claims, and maintenance tickets with state persistence and reversible undo tokens. |

---

## 🚀 How to Run the Demo

Return Detective is architected for **dual execution**: it can deploy to live Google Cloud infrastructure via Cloud Run and BigQuery, or run 100% locally with zero external cloud dependencies or billing needed.

### Option A: Running Locally (Instant One-Command Launch)

#### Prerequisites
- Python 3.11+
- Node.js 20+

```bash
# 1. Clone repository
git clone https://github.com/your-org/return-detective.git
cd return-detective

# 2. Run the automated all-in-one local launcher
./start_local.sh
```

The script automatically:
1. Creates a Python virtual environment and installs all dependencies (`fastapi`, `duckdb`, `pydantic`, `pandas`, `pillow`, `google-genai`).
2. Installs Node.js packages and builds the Next.js web application.
3. Launches **Store Action API** on `http://localhost:8000` (Swagger docs at `/docs`).
4. Launches **Detective Runner Service** on `http://localhost:8001`.
5. Launches **Next.js Web Dashboard** on `http://localhost:3000`.

Open your browser to **`http://localhost:3000?demo=1`** to view the live dashboard with floating demo controls.

---

### Option B: Deploying to Google Cloud

#### Prerequisites
- Google Cloud Project with billing enabled
- `gcloud` CLI authenticated (`gcloud auth login`)
- Service account permissions for Cloud Run, BigQuery, Firestore, and Vertex AI

```bash
# 1. Configure environment variables
cp .env.example .env
# Edit .env with your GCP PROJECT_ID

# 2. Run infrastructure provisioning script
chmod +x infra/setup.sh
./infra/setup.sh

# 3. Generate data & backfill forensic embeddings
source .venv/bin/activate
python -m data.generator
python -m data.photos.assign_photos
python -m data.backfill_forensics

# 4. Deploy all microservices to Cloud Run
chmod +x infra/deploy.sh
./infra/deploy.sh
```

---

## 🧪 Automated Scenario Verification (Test Suite)

Run the comprehensive end-to-end integration test suite, which runs **3 consecutive iterations** of all 6 scenarios and the +7 day post-intervention audit:

```bash
source .venv/bin/activate
PYTHONPATH=. python -m tests.test_scenarios
```

Output:
```
================================================================================
🧪 EXECUTING 3 CONSECUTIVE END-TO-END SCENARIO VALIDATION RUNS
================================================================================
--- Running Full Scenario Suite Iteration 1 of 3 ---
✓ Iteration 1 PASSED cleanly with 100% scenario accuracy!
--- Running Full Scenario Suite Iteration 2 of 3 ---
✓ Iteration 2 PASSED cleanly with 100% scenario accuracy!
--- Running Full Scenario Suite Iteration 3 of 3 ---
✓ Iteration 3 PASSED cleanly with 100% scenario accuracy!
================================================================================
🎉 ALL 3 CONSECUTIVE TEST RUNS PASSED! 0 FLAKY SCENARIOS DETECTED!
================================================================================
```

---

## 👥 Team & Submission Info
- **Product:** DarkOps
- **Team:** SherlOps (AI Builder Cup 2026)
- **Primary Google Cloud Stack:** Gemini 2.5 (Pro & Flash), BigQuery, BigQuery ML, BigQuery VECTOR_SEARCH, Cloud Run, Firestore, Cloud Storage, Pub/Sub, Cloud Scheduler, Cloud Trace.
- **License:** Apache 2.0
