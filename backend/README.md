# PatientTriage.ai Backend

> ⚠️ **PROTOTYPE — Synthetic Data Only — NOT for Clinical Use**

AI-assisted emergency department triage decision support system.

## Overview
PatientTriage.ai helps ED staff prioritize patients through deterministic safety rules, risk scoring, and confidence assessment. The system provides recommendations — clinicians always make final decisions.

## Architecture

```
Patient Input → Safety Engine → Risk Engine → Confidence Engine → Decision Engine → Queue
```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (recommended) or PostgreSQL 16

### Option A: Docker (Recommended)
```bash
# From project root (d:\P-D)
docker-compose up -d

# Wait for DB to be ready, then seed:
docker exec patienttriage_backend python scripts/seed_database.py
```

### Option B: Local Development
```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy env file
copy .env.example .env

# Start PostgreSQL (Docker)
docker run -d --name patienttriage_db \
  -e POSTGRES_USER=triage \
  -e POSTGRES_PASSWORD=triage \
  -e POSTGRES_DB=patienttriage \
  -p 5432:5432 postgres:16-alpine

# Run Alembic migrations
alembic upgrade head

# Seed data
python scripts/seed_database.py

# Start server
uvicorn app.main:app --reload --port 8000
```

### Verify
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Queue: http://localhost:8000/queue

## Demo Reset
```bash
python scripts/reset_database.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | System health |
| GET | /patients | List all patients |
| GET | /patients/{id} | Patient details |
| POST | /triage | Triage new patient |
| GET | /queue | Priority queue |
| GET | /alerts | Active alerts |
| POST | /alerts/{id}/acknowledge | Acknowledge alert |
| GET | /capacity | ED capacity |
| POST | /override | Clinician override |
| GET | /audit | Audit log |
| POST | /simulate/deterioration/{id} | Demo deterioration |
| POST | /simulate/surge | Demo surge |
| WS | /ws/queue | Real-time updates |

## Demo Scenarios

### Scenario 1: Deterioration Demo
```bash
# Trigger deterioration for P009 (Carlos Rivera)
curl -X POST http://localhost:8000/simulate/deterioration/P009
# Result: Priority HIGH → CRITICAL, alert fired, queue updated
```

### Scenario 2: Critical Patient Triage
```bash
curl -X POST http://localhost:8000/triage \
  -H 'Content-Type: application/json' \
  -d '{"age":62,"gender":"male","chiefComplaint":"Breathlessness","symptoms":["shortness_of_breath","weakness"],"historyAvailable":true,"medicalHistory":["hypertension"],"vitals":{"heartRate":128,"systolicBp":85,"diastolicBp":52,"spo2":89,"temperature":38.2,"respiratoryRate":30}}'
```

### Scenario 3: Clinician Override
```bash
curl -X POST http://localhost:8000/override \
  -H 'Content-Type: application/json' \
  -d '{"patientId":"P009","assessmentId":"...","newPriority":"HIGH","reason":"Clinician reassessment","clinicianId":"DR_DEMO"}'
```

## Running Tests
```bash
pytest tests/ -v
```

## Safety Architecture

The Safety Engine establishes a **minimum priority floor** based on vital sign thresholds:
- Uses age-appropriate thresholds (Pediatric / Adult / Geriatric)
- Multiple critical conditions → CRITICAL floor
- Safety floor can only raise priority, never lower it

> ⚠️ Thresholds are for prototype demonstration only and are NOT clinically validated.

## Clinical Disclaimer

This is a prototype system using entirely synthetic patient data. It is NOT:
- Clinically validated
- Approved for patient care
- A diagnostic tool
- A replacement for clinical judgment

All triage recommendations require clinician review.
