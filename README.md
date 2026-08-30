PatientTriage.ai

⚠️ Prototype — synthetic data only. Not for clinical use.

AI-assisted Emergency Department patient prioritization and operational management system.

PatientTriage.ai is designed to help Emergency Department teams manage patient priority in a changing environment by combining a deterministic decision pipeline, real-time operational state, and an LLM-based explanation layer.

The core priority decision is made by deterministic engines. The LLM does not determine or override patient priority — it explains, summarizes, and assists. Clinicians retain final authority through an explicit human-in-the-loop override path.

📸 Product Screenshots

Replace the six placeholders below with screenshots from the running application.
Recommended location: docs/screenshots/

1. Command Center



Primary operational view showing the current ED state, patient priorities, alerts, capacity and resource information.

2. Patient & Triage Assessment



Patient-level view for assessment, vitals, triage status and decision information.

3. Dynamic Priority Queue



Live-ranked patient queue generated from the system's deterministic decision pipeline.

4. Beds & Capacity Management



Operational capacity view showing bed availability, occupancy and resource state.

5. Alerts & Deterioration



Alerts and deterioration-related operational information requiring staff attention.

6. AI Decision Trace



Transparent explanation of the structured system decision, including the factors that contributed to the recommendation and the AI-generated explanation.

1. Problem

Emergency Department prioritization is not a one-time decision.

Patients can arrive with incomplete or ambiguous information, patient condition can change while waiting, new patients can arrive, and beds and other resources can become constrained.

A useful operational system therefore needs to do more than generate an initial triage result.

PatientTriage.ai addresses this by providing a continuously updated operational layer around deterministic patient prioritization.

2. Solution

PatientTriage.ai combines patient assessment with operational ED information to support:

Patient risk and safety assessment

Confidence assessment

Deterioration monitoring

Dynamic priority queue management

Bed and capacity management

Resource awareness

Real-time operational updates

Clinician overrides

Decision and action auditing

AI-generated explanations and summaries

The system is designed around a simple principle:

AI recommends. Safety rules protect. Clinicians decide.

3. Core Design Principle

Deterministic decisions. AI-assisted understanding. Human authority.

PatientTriage.ai intentionally separates decision-making from language generation.

┌──────────────────────────────┐
│   Deterministic Engine       │
│                              │
│ Safety                       │
│ Risk                         │
│ Confidence                   │
│ Deterioration               │
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
         ┌─────┴─────┐
         ▼           ▼
      Accept       Override
         │           │
         └─────┬─────┘
               ▼
             Audit

What the LLM does

Explains deterministic decisions

Summarizes patient context

Assists clinician understanding

What the LLM does not do

Determine patient priority

Override the deterministic engine

Replace clinician authority

This separation is a core architectural property of the system.

4. System Architecture

High-Level Decision Flow

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
                     ┌────────────┴────────────┐
                     │                         │
                     ▼                         ▼
            ┌─────────────────┐       ┌────────────────┐
            │ Operational     │       │  LLM Service   │
            │ Engines         │       │ Explanation    │
            │                 │       │ & Summary      │
            └────────┬────────┘       └───────┬────────┘
                     │                        │
                     └────────────┬───────────┘
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

5. Decision & Operational Engines

The backend contains nine dedicated engines:

Engine

Responsibility

safety_engine

Safety assessment

risk_engine

Risk assessment

confidence_engine

Confidence assessment

decision_engine

Deterministic priority decision

deterioration_engine

Deterioration assessment

alert_engine

Operational alerts

capacity_engine

Capacity/resource assessment

queue_engine

Priority queue management

recommendation_engine

Operational recommendations

These engines form the deterministic and operational core of PatientTriage.ai.

The LLM explanation layer is implemented separately through the backend service layer.

6. Key Capabilities

🩺 Patient Triage

Run a patient through the triage assessment pipeline and generate a deterministic priority decision.

🚨 Safety & Risk Assessment

Evaluate patient information through dedicated safety, risk and confidence engines.

📈 Deterioration Monitoring

Account for changes in patient condition as part of the operational decision pipeline.

📋 Dynamic Priority Queue

Maintain a live-ranked queue of patients based on the system's decision engines.

🛏️ Capacity Management

Track beds, occupancy, staff/equipment resources and capacity-related recommendations.

⚡ Real-Time Updates

Use WebSockets to broadcast queue, alert and capacity changes to connected clients.

👨‍⚕️ Clinician Override

Provide an explicit path for clinicians to override a system-generated priority.

📝 Audit Trail

Record engine decisions and clinician actions for traceability.

🤖 AI Explanation Layer

Use an LLM to explain and summarize system outputs without making the underlying priority decision.

7. Patient Lifecycle

PatientTriage.ai treats the patient and the assessment as separate concepts.

PATIENT
   │
   ├── Assessment 1
   │      ├── Symptoms
   │      ├── Vitals
   │      └── Triage Decision
   │
   ├── Assessment 2
   │      ├── Updated Vitals
   │      ├── Updated Condition
   │      └── New Decision
   │
   └── Assessment 3
          ├── Updated Vitals
          └── New Decision

This allows the system to represent an evolving patient state rather than treating every reassessment as a completely new patient event.

8. Real-Time Operational Layer

PatientTriage.ai is not limited to static triage results.

The backend exposes a WebSocket connection for real-time operational updates:

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

This allows the Command Center and other frontend views to react to changing system state without relying exclusively on manual refreshes.

9. Capacity & Resource Management

PatientTriage.ai includes an operational capacity layer for monitoring hospital resources.

The capacity layer supports:

Bed availability

Bed occupancy

Bed allocation

Bed release

Bed reallocation

General/ICU capacity totals

Resource state

Capacity-related recommendations

The objective is to provide operational context alongside patient priority.

A patient recommendation should therefore be interpreted together with the current ED capacity rather than in isolation.

10. Priority Queue

The queue engine maintains the operational priority order generated by the deterministic decision pipeline.

The queue provides a continuously updated view of:

Patient priority

Current status

Relative urgency

Operational changes

Alerts affecting attention

Capacity context

The queue is intended as a decision-support view, not an autonomous treatment allocation system.

11. Alerts & Deterioration

The deterioration and alert layers provide operational visibility when patient state changes.

Conceptually:

Patient State
     │
     ▼
Updated Information
     │
     ▼
Deterioration Assessment
     │
     ├───────────────┐
     ▼               ▼
No significant     Change detected
change                 │
                       ▼
                  Alert / Decision
                       │
                       ▼
                 Clinician Review

The alert layer makes important changes visible to the clinical/operational team.

12. AI Explanation Layer

The AI layer is intentionally separated from the medical decision pipeline.

Structured System Decision
          │
          ▼
      LLM Service
          │
          ▼
Human-readable Explanation
          │
          ▼
       Clinician

The explanation layer can:

Summarize patient context

Explain the structured decision

Present relevant contributing factors

Assist understanding of system output

The LLM is not responsible for assigning the underlying patient priority.

13. Human-in-the-Loop

PatientTriage.ai keeps clinicians in control.

System Recommendation
        │
        ▼
Clinician Review
     │       │
     │       └── Override
     │
     └── Accept
             │
             ▼
          Audit Log

A clinician can review the system recommendation and take the appropriate action.

Overrides are recorded for traceability.

14. AI Decision Trace

PatientTriage.ai is designed to make the reasoning behind a system-generated priority visible.

A decision trace can connect:

Patient Information
       ↓
Safety Assessment
       ↓
Risk Assessment
       ↓
Confidence
       ↓
Deterioration
       ↓
Decision
       ↓
Queue Position
       ↓
AI Explanation
       ↓
Clinician Action

This provides a structured path for understanding why a patient's operational priority changed.

15. Application Structure

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
├── docs/
│   └── screenshots/
│
└── README.md

Backend

Built with FastAPI + SQLAlchemy.

engines/ — deterministic and operational decision engines

api/ — FastAPI routers

services/ — business logic and LLM integration

models/ — SQLAlchemy database models

schemas/ — Pydantic request/response schemas

realtime/ — WebSocket connection management

Frontend

Built with Next.js 16 App Router + Tailwind CSS.

app/ — application pages

hooks/ — data-fetching and WebSocket hooks

lib/api.ts — typed backend API client

components/ — reusable interface components

16. Frontend Views

The frontend includes:

/dashboard
/command-center
/queue
/patients
/triage
/capacity
/alerts
/audit
/surge

The Command Center provides the primary operational view of the system.

17. Technology Stack

Layer

Technology

Frontend

Next.js 16

UI

Tailwind CSS

Backend

FastAPI

Language

Python 3.11+

ORM

SQLAlchemy

Validation

Pydantic

Local Database

SQLite

Production Database

PostgreSQL

Realtime

WebSockets

LLM

Hugging Face / Qwen2.5-Instruct

Testing

Pytest

18. API

The backend exposes REST endpoints across the main operational areas.

Area

Endpoint

Purpose

Triage

POST /triage/assess

Run a patient through the engine pipeline

Queue

GET /queue

Retrieve the live-ranked priority queue

Patients

GET /patients/{id}

Retrieve patient details, latest assessment and vitals

Patients

PATCH /patients/{id}/status

Change patient status

Capacity

GET /capacity

Retrieve beds, resources and occupancy

Capacity

POST /capacity/beds

Add a bed

Capacity

DELETE /capacity/beds/{id}

Remove a bed

Capacity

PUT /capacity/beds/totals

Set General/ICU bed totals

Capacity

POST /capacity/beds/allocate

Allocate a bed

Capacity

POST /capacity/beds/release

Release a bed

Capacity

POST /capacity/beds/reallocate

Reallocate a bed

Override

POST /override

Record a clinician priority override

Audit

GET /audit

Retrieve the audit trail

Interactive API documentation is available through FastAPI:

http://localhost:8000/docs

19. Synthetic Data

The prototype uses synthetic patient data for demonstration and engineering evaluation.

Synthetic data is used to demonstrate:

Multiple patient states

Triage decisions

Queue behavior

Vital observations

Capacity states

Alerts

Operational scenarios

No real patient information should be used with this prototype.

20. Getting Started

Prerequisites

Tool

Version

Purpose

Python

3.11+

Backend

Node.js

20+

Frontend

npm

10+

Frontend dependencies

VS Code

Latest

Recommended development environment

Docker and PostgreSQL are not required for local development.

The local backend uses a SQLite database:

backend/patienttriage.db

21. Run Locally

1. Clone the repository

git clone <repository-url>
cd PatientTriage

Open the root PatientTriage/ folder in VS Code.

2. Start the Backend

cd backend

Create a virtual environment.

Windows

python -m venv .venv
.venv\Scripts\activate

macOS / Linux

python -m venv .venv
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Seed synthetic data:

python scripts/seed_database.py

Start the API:

uvicorn app.main:app --reload --port 8000

Backend:

http://localhost:8000

API documentation:

http://localhost:8000/docs

3. Start the Frontend

Open a second terminal:

cd frontend

Install dependencies:

npm install

Start the development server:

npm run dev

Frontend:

http://localhost:3000

Command Center:

http://localhost:3000/command-center

Important: Start the backend before the frontend. The frontend depends on the backend API and WebSocket connection for its data.

22. Environment Configuration

Frontend configuration:

NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/queue

The backend's local environment is configured for SQLite.

Production-style PostgreSQL configuration is documented separately in backend/README.md.

23. Database Management

Seed synthetic data

cd backend
python scripts/seed_database.py

Reset and re-seed

cd backend
python scripts/reset_database.py

This resets the database and recreates the seeded environment.

24. Testing

Run the backend test suite:

cd backend
pytest -q

The repository contains tests covering:

Risk engine

Safety engine

Confidence engine

Deterioration engine

API behavior

Integration behavior

The test suite includes individual engine tests and broader API/integration coverage.

25. Development Workflow

For local development, use two VS Code terminals:

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

This keeps the frontend and backend visible within the same workspace.

26. Demonstration Workflow

A typical prototype demonstration can follow this sequence:

1. Open Command Center
        ↓
2. Review current patient queue
        ↓
3. Open a patient
        ↓
4. Review triage information and vitals
        ↓
5. Run / review the assessment
        ↓
6. Observe priority decision
        ↓
7. Review deterioration / alerts
        ↓
8. Check current bed and capacity state
        ↓
9. Open AI Decision Trace
        ↓
10. Review human-readable explanation
        ↓
11. Clinician accepts or overrides
        ↓
12. Action appears in audit trail

This demonstrates the complete relationship between patient state, deterministic decision-making, operational capacity, explanation and human oversight.

27. Safety & Scope

PatientTriage.ai is a prototype using synthetic patient data.

It is not a clinical system and should not be used to make real-world medical decisions.

The project demonstrates:

Deterministic patient prioritization

Operational ED queue management

Resource/capacity visibility

Real-time system updates

Human-in-the-loop overrides

AI-assisted explanations

Decision and action auditing

Clinical deployment would require substantially more validation, governance, safety engineering, security controls, regulatory consideration and clinical evaluation than is represented by this prototype.

28. Key Safety Principles

PatientTriage.ai follows these architectural principles:

1. Deterministic priority

The underlying priority decision is produced by dedicated decision engines rather than the language model.

2. Safety-first architecture

Safety logic is separated from general risk assessment.

3. Human authority

Clinicians retain the ability to accept or override system recommendations.

4. Explainability

System outputs can be presented through a structured decision trace and AI-generated explanation.

5. Auditability

Important system decisions and clinician actions are recorded.

6. Prototype isolation

The current implementation uses synthetic data and is intended for demonstration and engineering evaluation.

29. Roadmap

Phase 1 — Prototype

Patient prioritization

Safety and risk engines

Confidence assessment

Deterioration assessment

Dynamic queue

Capacity management

Alerts

Recommendations

Real-time updates

Clinician override

Audit trail

AI explanation

Phase 2 — Controlled Hospital Pilot

Real hospital data integration

EHR/EMR integration

Real-time clinical device integration

Clinical validation

Workflow validation

Security and access-control hardening

Model monitoring

Clinician feedback

Phase 3 — Scaled Deployment

Multi-hospital deployment

Advanced capacity planning

Predictive operational analytics

Cross-site benchmarking

Continuous model monitoring and improvement

30. Project Status

Current status: Prototype

PatientTriage.ai is a full-stack prototype consisting of:

FastAPI backend

Deterministic triage and operational engines

SQLAlchemy persistence layer

Real-time WebSocket layer

Next.js operational dashboard

LLM explanation service

Clinician override workflow

Audit workflow

Capacity and bed management

Synthetic seeded data

Backend unit, API and integration tests

31. Project Vision

From patient triage to intelligent Emergency Department orchestration.

PatientTriage.ai aims to provide healthcare teams with a continuously updated operational picture of:

Patient Condition
       +
Clinical Risk
       +
Deterioration
       +
Priority Queue
       +
Beds & Resources
       +
Operational Alerts
       ↓
Actionable Recommendation
       ↓
Clinician Review
       ↓
Auditable Decision

The long-term objective is not to replace clinical judgment.

It is to give Emergency Department teams better information, better visibility and better operational decision support at the moment it matters.

Disclaimer

PatientTriage.ai is a prototype intended for demonstration and engineering evaluation. It uses synthetic data and is not intended for clinical use or real-world medical decision-making.
