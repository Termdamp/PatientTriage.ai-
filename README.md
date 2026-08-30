# PatientTriage

> ⚠️ **Prototype — synthetic data only. Not for clinical use.**

**AI-assisted Emergency Department patient prioritization and operational management system.**

PatientTriage is designed to help Emergency Department teams manage patient priority in a changing environment by combining a **deterministic decision pipeline**, **real-time operational state**, and an **LLM-based explanation layer**.

The core priority decision is made by deterministic engines. The LLM does **not** determine or override patient priority — it explains, summarizes, and assists. **Clinicians retain final authority** through an explicit human-in-the-loop override path.

```text
Patient Data
     │
     ▼
Safety Engine
     │
     ▼
Risk Engine
     │
     ▼
Confidence Engine
     │
     ▼
Decision Engine
     │
     ▼
Priority Queue
     │
     ▼
AI Explanation
     │
     ▼
Clinician
```

---

## Why PatientTriage?

Emergency Department prioritization is not a one-time decision.

Patient condition can change, new patients can arrive, existing patients can deteriorate, and available beds and resources can shift. A useful operational system therefore needs to do more than produce an initial triage score.

PatientTriage brings together:

- patient risk and safety assessment
- confidence in the available information
- deterioration monitoring
- dynamic queue prioritization
- capacity and bed management
- real-time operational updates
- clinician overrides
- decision and action auditing
- AI-generated explanations and summaries

The goal is to provide a **transparent operational layer around deterministic prioritization**, while keeping clinicians in control.

---

# Core Design Principle

### Deterministic decisions. AI-assisted understanding. Human authority.

PatientTriage intentionally separates **decision-making** from **language generation**.

```text
┌──────────────────────────────┐
│   Deterministic Engine       │
│                              │
│ Safety                       │
│ Risk                         │
│ Confidence                   │
│ Deterioration                │
│ Capacity                     │
│ Decision                     │
│ Queue                        │
│ Alerts                       │
│ Recommendations              │
└──────────────┬───────────────┘
               │
               ▼
        Priority / State
               │
               ▼
┌──────────────────────────────┐
│        LLM Layer             │
│                              │
│ Explain                      │
│ Summarize                    │
│ Assist                       │
└──────────────┬───────────────┘
               │
               ▼
          ┌──────────┐
          │ Clinician│
          └────┬─────┘
               │
        ┌──────┴──────┐
        ▼             ▼
     Accept         Override
        │             │
        └──────┬──────┘
               ▼
             Audit
```

### What the LLM does

- Explains deterministic decisions
- Summarizes patient context
- Assists clinician understanding

### What the LLM does not do

- Determine patient priority
- Override the deterministic engine
- Replace clinician authority

This separation is a core architectural property of the system.

---

# Key Capabilities

### 🩺 Patient Triage

Run a patient through the triage assessment pipeline and generate a deterministic priority decision.

### 🚨 Safety & Risk Assessment

Evaluate patient information through dedicated safety, risk, and confidence engines.

### 📈 Deterioration Monitoring

Account for changes in patient condition as part of the operational decision pipeline.

### 📋 Dynamic Priority Queue

Maintain a live-ranked queue of patients based on the system's decision engines.

### 🛏️ Capacity Management

Track beds, occupancy, staff/equipment resources, and capacity-related recommendations.

### ⚡ Real-Time Updates

Use WebSockets to broadcast queue, alert, and capacity changes to connected clients.

### 👨‍⚕️ Clinician Override

Provide an explicit path for clinicians to override a system-generated priority.

### 📝 Audit Trail

Record engine decisions and clinician actions for traceability.

### 🤖 AI Explanation Layer

Use an LLM to explain and summarize system outputs without making the underlying priority decision.

---

# System Architecture

## High-Level Flow

```text
                         ┌──────────────────┐
                         │   Patient Data   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Safety Engine   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Risk Engine    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │Confidence Engine │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Decision Engine  │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Priority Queue  │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
           ┌─────────────────┐         ┌────────────────┐
           │  Alert / Other  │         │  LLM Service   │
           │ Operational     │         │  Explanation   │
           │ Engines         │         │  & Summary     │
           └────────┬────────┘         └───────┬────────┘
                    │                          │
                    └────────────┬─────────────┘
                                 ▼
                       ┌────────────────────┐
                       │  Clinician / UI    │
                       └─────────┬──────────┘
                                 │
                         Override / Action
                                 │
                                 ▼
                         ┌────────────────┐
                         │   Audit Trail  │
                         └────────────────┘
```

---

# Decision & Operational Engines

The backend contains nine dedicated engines:

| Engine | Responsibility |
|---|---|
| `safety_engine` | Safety assessment |
| `risk_engine` | Risk assessment |
| `confidence_engine` | Confidence assessment |
| `decision_engine` | Deterministic priority decision |
| `deterioration_engine` | Deterioration assessment |
| `alert_engine` | Operational alerts |
| `capacity_engine` | Capacity/resource assessment |
| `queue_engine` | Priority queue management |
| `recommendation_engine` | Operational recommendations |

The engines form the deterministic and operational core of PatientTriage.

The LLM explanation layer is implemented separately through the backend service layer.

---

# Real-Time Operational Layer

PatientTriage is not limited to static triage results.

The backend exposes a WebSocket connection for real-time operational updates:

```text
Backend
   │
   ├── Queue changes
   ├── Alert changes
   └── Capacity changes
            │
            ▼
       WebSocket
            │
            ▼
        Frontend
```

This allows the Command Center and other frontend views to react to changing system state without relying exclusively on manual refreshes.

---

# Application Structure

```text
PatientTriage/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── engines/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── realtime/
│   │
│   ├── scripts/
│   ├── tests/
│   └── README.md
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   └── README.md
│
└── README.md
```

### Backend

Built with **FastAPI + SQLAlchemy**.

- `engines/` — nine deterministic/operational decision engines
- `api/` — FastAPI routers
- `services/` — business logic and LLM integration
- `models/` — SQLAlchemy database models
- `schemas/` — Pydantic request/response schemas
- `realtime/` — WebSocket connection management

### Frontend

Built with **Next.js 16 App Router + Tailwind CSS**.

- `app/` — application pages
- `hooks/` — data-fetching and WebSocket hooks
- `lib/api.ts` — typed backend API client
- `components/` — reusable interface components

---

# Frontend Views

The frontend currently includes:

```text
/dashboard
/command-center
/queue
/patients
/triage
/capacity
/alerts
/audit
/surge
```

The **Command Center** provides the primary operational view of the system.

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 |
| UI | Tailwind CSS |
| Backend | FastAPI |
| Language | Python 3.11+ |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Local Database | SQLite |
| Production Database | PostgreSQL |
| Realtime | WebSockets |
| LLM | Hugging Face / Qwen2.5-Instruct |
| Testing | Pytest |

---

# API

The backend exposes REST endpoints across the main operational areas.

| Area | Endpoint | Purpose |
|---|---|---|
| Triage | `POST /triage/assess` | Run a patient through the engine pipeline |
| Queue | `GET /queue` | Retrieve the live-ranked priority queue |
| Patients | `GET /patients/{id}` | Retrieve patient details, latest assessment and vitals |
| Patients | `PATCH /patients/{id}/status` | Change patient status |
| Capacity | `GET /capacity` | Retrieve beds, resources and occupancy |
| Capacity | `POST /capacity/beds` | Add a bed |
| Capacity | `DELETE /capacity/beds/{id}` | Remove a bed |
| Capacity | `PUT /capacity/beds/totals` | Set General/ICU bed totals |
| Capacity | `POST /capacity/beds/allocate` | Allocate a bed |
| Capacity | `POST /capacity/beds/release` | Release a bed |
| Capacity | `POST /capacity/beds/reallocate` | Reallocate a bed |
| Override | `POST /override` | Record a clinician priority override |
| Audit | `GET /audit` | Retrieve the audit trail |

Interactive API documentation is available through FastAPI once the backend is running:

```text
http://localhost:8000/docs
```

---

# Getting Started

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Backend |
| Node.js | 20+ | Frontend |
| npm | 10+ | Frontend dependencies |
| VS Code | Latest | Recommended development environment |

Docker and PostgreSQL are **not required for local development**.

The local backend uses a SQLite database:

```text
backend/patienttriage.db
```

Production-style Docker/PostgreSQL configuration is documented separately in `backend/README.md`.

---

# Run Locally

## 1. Clone the repository

```bash
git clone <repository-url>
cd PatientTriage
```

Open the **root `PatientTriage/` folder** in VS Code rather than opening `backend/` or `frontend/` separately.

---

## 2. Start the Backend

Open a terminal:

```bash
cd backend
```

Create and activate a virtual environment:

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The local `.env` is configured to use SQLite.

Seed the database with synthetic patients, beds, and resources:

```bash
python scripts/seed_database.py
```

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

## 3. Start the Frontend

Open a second terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Frontend:

```text
http://localhost:3000
```

Open the Command Center:

```text
http://localhost:3000/command-center
```

> **Important:** Start the backend before the frontend. The frontend depends on the backend API and WebSocket connection for its data.

---

# Environment Configuration

For local development, the frontend is configured to communicate with:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/queue
```

The backend's local environment is configured for SQLite.

See the backend-specific README for the PostgreSQL/production configuration.

---

# Database Management

## Seed synthetic data

```bash
cd backend
python scripts/seed_database.py
```

## Reset and re-seed

To wipe the existing database and recreate the seeded environment:

```bash
cd backend
python scripts/reset_database.py
```

This resets all tables and re-seeds the database.

---

# Testing

Run the backend test suite:

```bash
cd backend
pytest -q
```

The repository currently contains **31 backend tests** covering:

- Risk engine
- Safety engine
- Confidence engine
- Deterioration engine
- API behavior
- Integration behavior

The test suite includes both individual engine tests and broader API/integration coverage.

---

# Development Workflow

For the simplest local development setup, use two VS Code terminals:

```text
┌─────────────────────────────┐
│ Terminal 1                  │
│                             │
│ cd backend                  │
│ uvicorn app.main:app        │
└──────────────┬──────────────┘
               │
               │ HTTP / WebSocket
               ▼
┌─────────────────────────────┐
│ Terminal 2                  │
│                             │
│ cd frontend                 │
│ npm run dev                 │
└─────────────────────────────┘
```

This keeps both frontend and backend visible within the same VS Code workspace.

---

# Safety & Scope

PatientTriage is a **prototype** using **synthetic patient data**.

It is **not a clinical system** and should not be used to make real-world medical decisions.

The project demonstrates an approach to:

- deterministic patient prioritization
- operational ED queue management
- resource/capacity visibility
- real-time system updates
- human-in-the-loop overrides
- AI-assisted explanations

Clinical deployment would require substantially more validation, governance, safety engineering, and regulatory consideration than is represented by this prototype.

---

# Troubleshooting

### Frontend loads but shows no data / "Failed to fetch"

Make sure the backend is running on the address configured in:

```text
frontend/.env.local
```

By default:

```text
http://localhost:8000
```

### `ModuleNotFoundError` on backend start

Make sure the virtual environment is activated and dependencies are installed:

```bash
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
```

### Empty queue after seeding

Check the backend terminal for errors during:

```bash
python scripts/seed_database.py
```

If the database already contains data, reset and re-seed:

```bash
python scripts/reset_database.py
```

### Port already in use

Change the backend port:

```bash
uvicorn app.main:app --reload --port <PORT>
```

Then update:

```text
NEXT_PUBLIC_API_URL
NEXT_PUBLIC_WS_URL
```

in `frontend/.env.local` accordingly.

---

# Project Status

**Current status: Prototype**

The repository is structured as a full-stack prototype consisting of:

- a FastAPI backend
- deterministic triage and operational engines
- a SQLAlchemy persistence layer
- a real-time WebSocket layer
- a Next.js operational dashboard
- an LLM explanation service
- clinician override and audit workflows
- seeded synthetic data
- backend unit, API, and integration tests

---

## Repository

```text
PatientTriage/
├── backend/
│   └── FastAPI + SQLAlchemy + decision/operational engines
│
├── frontend/
│   └── Next.js + Tailwind operational dashboard
│
└── README.md
```

> **PatientTriage is a prototype intended for demonstration and engineering evaluation. It is not intended for clinical use.**
