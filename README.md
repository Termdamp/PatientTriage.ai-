# PatientTriage.ai

**A human-in-the-loop, safety-first decision-support system that continuously combines patient risk, uncertainty, deterioration, and waiting time to dynamically surface who needs attention — while keeping every recommendation explainable, overridable, and auditable.**

> ⚠️ **Prototype Disclaimer**
> This is a hackathon prototype (Round 2 submission) built on **synthetic, simulated data**. No clinical thresholds, scoring weights, rules, or outputs in this repository are clinically validated. Nothing here constitutes medical advice or a diagnostic tool. Real-world deployment would require clinical validation, prospective evaluation, regulatory review, formal governance, and integration with validated hospital systems.

---

## Table of Contents

- [Problem](#problem)
- [Solution](#solution)
- [Core Design Principle: Triage as a Continuous Process](#core-design-principle-triage-as-a-continuous-process)
- [Human-in-the-Loop Philosophy](#human-in-the-loop-philosophy)
- [System Architecture](#system-architecture)
- [Safety-First Engine Design](#safety-first-engine-design)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [API Reference](#api-reference)
- [Getting Started](#getting-started)
- [Synthetic Dataset & Demo Scenarios](#synthetic-dataset--demo-scenarios)
- [Main Demo Flow](#main-demo-flow)
- [Testing](#testing)
- [Deployment](#deployment)
- [Data Protection & Regulatory Assumptions](#data-protection--regulatory-assumptions)
- [Roadmap](#roadmap)
- [Business Case Summary](#business-case-summary)
- [Team](#team)
- [License](#license)

---

## Problem

When an emergency department is overwhelmed, patient sequencing depends heavily on one nurse's judgment under pressure. Traditional triage is largely a **snapshot**: a patient is assessed once at arrival, assigned a priority, and then waits — with no systematic mechanism to notice that their condition is quietly worsening in the waiting room. Mis-prioritization, or missed deterioration, can cost lives.

No two EDs look alike — patient mix, staffing, and technical maturity vary — and any real system has to work with:

- Overlapping, ambiguous, or under-reported symptoms
- Vital-sign thresholds that differ by age group (pediatric vs. adult vs. geriatric)
- Wildly inconsistent data availability (returning patients with rich history vs. first-time patients with almost nothing)
- Decisions that must be explainable within seconds, by a clinician juggling several patients at once
- The asymmetric cost of under-triage vs. over-triage — missing a critical case is categorically worse than over-prioritizing a minor one

## Solution

PatientTriage.ai is an AI-assisted decision-support tool that helps clinicians prioritize and route patients as they arrive, and **keeps watching them after that first triage**. It follows one governing rule:

**AI recommends → Clinician reviews → Clinician decides.**

The AI never autonomously diagnoses, discharges, or moves a patient. It analyzes, ranks, flags concerning patterns, estimates risk and its own uncertainty, explains its reasoning, and alerts a clinician — who accepts, overrides, or reassesses. Every one of those steps is logged.

## Core Design Principle: Triage as a Continuous Process

| Traditional Triage | PatientTriage.ai |
|---|---|
| Patient arrives → Initial triage → Priority assigned → Patient waits | Patient arrives → Initial triage → Priority assigned → **Continuous monitoring** → Detect deterioration / waiting-time breach → Alert clinician → Reassess → Reprioritize |

```
TRIAGE → PRIORITIZE → MONITOR → DETECT CHANGE → ALERT → REASSESS → REPRIORITIZE
```

## Human-in-the-Loop Philosophy

**The AI does:**
Analyze · Rank · Detect concerning patterns · Detect deterioration · Estimate risk · Estimate its own uncertainty · Explain its reasoning · Alert clinicians · Surface capacity conflicts

**The AI never does:**
Autonomously diagnose · Autonomously discharge a patient · Autonomously move a patient without approval · Make an irreversible clinical decision · Replace licensed clinical judgment

```
AI recommendation → Clinician review → Accept / Override / Reassess → Audit log
```

## System Architecture

```
PATIENT DATA
      ↓
DATA QUALITY / INTAKE
      ↓
 ┌───────────────┐
 │               │
 ▼               ▼
SAFETY ENGINE   RISK ENGINE
 │               │
 │               ▼
 │          RISK SCORE
 │               │
 └───────┬───────┘
         ▼
CONFIDENCE ENGINE
         ↓
DECISION ENGINE
         ↓
DYNAMIC QUEUE
         ↓
 ┌───────┴────────┐
 ▼                ▼
WAITING        NEW VITALS
MONITORING          │
                    ▼
             DETERIORATION ENGINE
                    │
                    ▼
                ALERT ENGINE
                    │
                    ▼
               CLINICIAN
               /   |   \
          ACCEPT OVERRIDE REASSESS
                    │
                    ▼
                AUDIT LOG
```

Supporting engines run alongside the core pipeline: **Queue Engine**, **Waiting-Time Engine**, **Surge Engine**, **Capacity Engine**, **Override Engine**, and **Audit Engine**.

## Safety-First Engine Design

The system deliberately does **not** do `Patient → ML → Final Decision`. Two engines run in parallel and are then reconciled:

- **Risk Engine** asks: *"How risky does this patient appear?"* — an explainable, weighted scoring model over vitals, symptoms, age, and history.
- **Safety Engine** asks: *"Is there anything here that makes a low-priority recommendation unsafe?"* — a transparent, conservative, deterministic rule layer. It does **not** diagnose ("patient has sepsis"); it only flags ("concerning vital-sign pattern detected — do not downgrade without clinician reassessment").

The Safety Engine can establish a **safety floor** that the Risk Engine is not allowed to undercut:

```
Risk Engine   → LOW
Safety Floor  → HIGH
Final Priority → HIGH
```

A **Confidence Engine** then asks a distinct question — *"How confident are we, given the available information?"* — factoring in missing history, missing vitals, ambiguous symptoms, and data completeness. Critically: **high risk + low confidence never collapses into low urgency** — it triggers cautious escalation and review instead.

The **Decision Engine** combines Safety + Risk + Confidence + Deterioration + Waiting Time into a final priority, reasons, and a recommended action — all of it explainable and logged.

This design directly satisfies the brief's requirement to *deliberately bias toward escalation under uncertainty rather than optimize for average accuracy*.

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router) + React + TypeScript + Tailwind CSS |
| Backend | Python + FastAPI + Pydantic |
| Database | SQLite (dev/demo) — SQLAlchemy engine also supports PostgreSQL for production |
| Real-time | WebSockets (`/ws/queue`) |
| Decision logic | Deterministic rule engines (Safety, Risk, Confidence, Decision) — ML-ready, not ML-dependent |
| Optional explanation layer | LLM service (Hugging Face-hosted small language model) for natural-language summaries only — **never** the safety-critical decision path |
| Deployment | Vercel (frontend) · Render / Docker (backend) |

We deliberately kept safety-critical logic deterministic and auditable rather than routing it through an LLM or opaque ML model — explainability was prioritized over marginal accuracy gains, consistent with the brief's emphasis on seconds-level explainability and clinician trust.

## Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers: patients, triage, queue, alerts,
│   │   │                   # capacity, simulation, override, audit
│   │   ├── engines/        # safety_engine, risk_engine, confidence_engine,
│   │   │                   # decision_engine, deterioration_engine, queue_engine,
│   │   │                   # capacity_engine, alert_engine, recommendation_engine
│   │   ├── services/       # patient_service, triage_service, queue_service,
│   │   │                   # alert_service, audit_service, capacity_service,
│   │   │                   # monitoring_service (background reassessment loop),
│   │   │                   # simulation_service, llm_service
│   │   ├── models/         # SQLAlchemy models: patient, vital, assessment,
│   │   │                   # alert, override, audit, bed, capacity, resource
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── realtime/       # WebSocket connection manager
│   │   ├── core/           # config, database, logging
│   │   └── main.py         # app init, CORS, lifespan, auto-seeding, /health, /ws/queue
│   ├── data/synthetic/patients.json   # 20 hand-designed synthetic patients
│   ├── scripts/            # seed_database.py, reset_database.py
│   ├── tests/              # pytest suite (see Testing below)
│   ├── alembic/            # DB migrations
│   ├── requirements.txt
│   ├── Dockerfile / docker-compose.yml
│   └── render.yaml
└── frontend/
    ├── app/
    │   ├── command-center/  # ED Command Center overview
    │   ├── queue/           # Dynamic priority queue
    │   ├── patients/[id]/   # Patient detail view
    │   ├── triage/          # New patient intake / triage form
    │   ├── alerts/          # Deterioration & waiting-time alerts
    │   ├── capacity/        # Bed/resource capacity dashboard
    │   ├── surge/           # Surge simulation dashboard
    │   ├── audit/           # Audit log viewer
    │   └── dashboard/
    ├── components/          # queue, alerts, layout components
    ├── hooks/               # useTriage, usePatients, useQueue, useAlerts,
    │                        # useCapacity, useAudit, useWebSocket
    ├── lib/                 # api.ts, websocket.ts, constants.ts, formatters.ts
    └── types/               # shared TypeScript types
```

## API Reference

All endpoints are served by the FastAPI backend (default `http://localhost:8000`).

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service + database health check |
| GET | `/patients` | List patients (optional `?status=`) |
| GET | `/patients/{id}` | Patient detail |
| GET | `/patients/{id}/audit` | Audit trail for one patient |
| PATCH | `/patients/{id}/status` | Update patient status |
| POST | `/triage` | Submit new patient intake → returns priority, risk, confidence, reasons |
| GET | `/queue` | Current prioritized queue |
| GET | `/alerts` | List alerts (optional `?unacknowledged_only=true`) |
| POST | `/alerts/{id}/acknowledge` | Acknowledge an alert |
| GET | `/capacity` | Bed/resource capacity snapshot |
| PUT | `/capacity/resources` | Update resource levels |
| POST | `/capacity/beds` | Add beds |
| DELETE | `/capacity/beds/{bed_id}` | Remove a bed |
| POST | `/capacity/beds/allocate` | Allocate a bed to a patient |
| POST | `/capacity/beds/release` | Release a bed |
| POST | `/capacity/beds/reallocate` | Reallocate beds |
| PUT | `/capacity/beds/totals` | Set total bed counts |
| POST | `/override` | Record a clinician override |
| GET | `/audit` | Full audit log |
| POST | `/simulate/deterioration/{patient_id}` | Simulate patient deterioration |
| POST | `/simulate/surge` | Simulate a volume surge (e.g., 3×) |
| WS | `/ws/queue` | Real-time push: queue updates, alerts, deterioration, capacity changes |

## Getting Started

### Prerequisites

- **Python 3.11 or 3.12** (recommended — see note below)
- **Node.js 20+**
- npm

> **Note:** Use Python 3.11/3.12, not the newest Python release. Some dependencies (e.g., `pydantic-core`) may not yet ship prebuilt wheels for the very latest Python version on every OS, which forces a source build requiring a Rust/C++ toolchain. 3.11/3.12 have prebuilt wheels for everything in `requirements.txt`.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # defaults to SQLite — no external DB required
uvicorn app.main:app --reload --port 8000
```

On first boot, the app automatically creates tables and seeds 20 synthetic patients if the database is empty (see `app/main.py` → `_auto_seed_if_empty`). Visit `http://localhost:8000/health` to confirm it's running.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local       # NEXT_PUBLIC_API_URL / NEXT_PUBLIC_WS_URL
npm run dev
```

Visit `http://localhost:3000`.

### Docker (backend only, SQLite)

```bash
cd backend
docker compose up --build
```

## Synthetic Dataset & Demo Scenarios

`backend/data/synthetic/patients.json` contains 20 hand-designed patients covering every scenario the brief requires:

- Normal low-risk and clearly critical presentations
- Pediatric and geriatric cases with age-aware logic
- An ambiguous presentation (vague symptoms, low confidence)
- A zero-history, first-time patient
- Missing/incomplete vitals
- A deteriorating patient (progressive vital-sign trajectory)
- Waiting-time breach and stable-but-long-wait cases
- A capacity-conflict scenario
- High-risk/low-confidence vs. low-risk/high-confidence contrast pairs

`POST /simulate/surge` reproduces a ~3× volume surge for stress-testing the queue, alerts, and capacity dashboards. `POST /simulate/deterioration/{patient_id}` reproduces a step-by-step vital-sign decline to trigger the Deterioration Engine live during a demo.

## Main Demo Flow

The strongest way to present this prototype is as **one patient's journey**, not a feature checklist:

1. Patient **P0xx** (67, chest discomfort) arrives → initial triage returns **MODERATE**, confidence 88%.
2. New vitals come in showing a worsening trend (HR ↑, BP ↓, SpO₂ ↓) → the Deterioration Engine detects the trajectory.
3. Priority is escalated → patient jumps to the top of the dynamic queue.
4. An alert fires: *"Immediate clinician reassessment recommended."*
5. Clinician reviews and either **accepts** or **overrides** the recommendation, with a reason.
6. Every step — creation, assessment, vitals update, alert, review, override — is written to the **audit log**.
7. Trigger a **3× surge** to show how the queue, capacity, and alert volume behave under stress.

This single flow demonstrates initial triage, risk, confidence, continuous monitoring, deterioration detection, dynamic queueing, alerting, human-in-the-loop override, auditability, and surge handling in one narrative.

## Testing

```bash
cd backend
pytest
```

Covers: `test_safety_engine.py`, `test_risk_engine.py`, `test_confidence_engine.py`, `test_deterioration_engine.py`, `test_api.py`, `test_integration.py`.

## Deployment

- **Frontend:** Vercel (set `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_WS_URL` to your deployed backend).
- **Backend:** Render (see `render.yaml`) or any Docker host. Defaults to SQLite for demo simplicity; swap `DATABASE_URL` to a `postgresql+psycopg://...` connection string for a persistent/production data store — the app already normalizes `postgres://`/`postgresql://` URLs to the psycopg3 driver automatically.

> On free-tier hosts with an ephemeral disk, SQLite data resets on every restart — this is intentional for a demo, since the app re-seeds automatically on boot. For anything beyond a demo, attach a persistent disk or move to managed Postgres.

## Data Protection & Regulatory Assumptions

- **Assumed jurisdiction (illustrative):** HIPAA (US). Design choices — audit trail structure, override recording, data retention — should be reviewed against the actual jurisdiction of deployment (e.g., GDPR + national health law in the EU) before any real use.
- All patient data in this repository is **synthetic**; no real patient data is used or stored.
- The audit log is designed to answer, for every decision: *What data did the system have? What did it recommend? Why? How confident was it? What did the clinician do? When?*
- Every override captures: patient ID, AI recommendation, AI confidence, clinician's decision, override reason, actor, and timestamp — because clinical accountability requires the human decision, not just the AI's, to be reviewable.
- A production system would need: encryption at rest/in transit, role-based access control, authentication/authorization on every endpoint (not implemented in this prototype), consent management, and a formal data-retention policy.

## License

This project was built for a hackathon submission and is provided as-is for evaluation purposes.
