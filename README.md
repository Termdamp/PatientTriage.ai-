# PatientTriage

> ⚠️ **Prototype — synthetic data only. Not for clinical use.**

AI-assisted Emergency Department (ED) patient prioritization system. A **deterministic scoring/ranking engine** decides priority; an **LLM layer sits around it** to explain, summarize, and assist — it never overrides the engine. Clinicians retain final authority (human-in-the-loop) via an explicit override path.

```
Patient Data → Safety Engine → Risk Engine → Confidence Engine → Decision Engine → Priority Queue → AI Explanation → Clinician
```

## Repository layout

```
PatientTriage/
├── backend/     FastAPI + SQLAlchemy service, the 9 decision engines, WebSocket queue updates
├── frontend/    Next.js 16 (App Router) + Tailwind dashboard, incl. the Command Center
└── README.md    You are here
```

Each half also has its own more detailed `README.md` — this file is the single "how do I get this running" entry point for both.

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | backend |
| Node.js | 20+ | frontend (Next.js 16 requires it) |
| npm | 10+ | ships with Node |
| VS Code | latest | recommended extensions below |

No Docker or PostgreSQL required for local dev — the backend is pre-configured to use a local **SQLite** file (`backend/patienttriage.db`) via `backend/.env`. Docker/Postgres is only needed if you want to mirror the production setup (see `backend/README.md`).

### Recommended VS Code extensions
- **Python** (`ms-python.python`) + **Pylance** — backend
- **ESLint** (`dbaeumer.vscode-eslint`) and **Tailwind CSS IntelliSense** (`bradlc.vscode-tailwindcss`) — frontend
- **Thunder Client** or **REST Client** — handy for poking the API directly

---

## Running it in VS Code

Open the **`PatientTriage/`** folder itself (not `backend/` or `frontend/` individually) as your VS Code workspace, so both halves are visible in the Explorer. Then use two integrated terminals side by side (`` Ctrl+` ``, then the split-terminal icon, or `Terminal → New Terminal` twice).

### Terminal 1 — Backend (FastAPI)

```bash
cd backend

# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. .env already exists and points at SQLite — no edits needed for local dev.
#    (backend/.env.example shows the Postgres variant if you switch later.)

# 4. Seed the database with synthetic patients/beds/resources
python scripts/seed_database.py

# 5. Start the API with hot reload
uvicorn app.main:app --reload --port 8000
```

In VS Code: once `.venv` exists, the Python extension will prompt to select it as the workspace interpreter (bottom-right status bar, or `Ctrl+Shift+P` → *Python: Select Interpreter*) — pick `backend/.venv`. That gets you linting/debugging against the right environment, and you can also run/debug `uvicorn` via a `launch.json` if you prefer F5 over the terminal.

The API is now live at **http://localhost:8000**, with interactive docs at **http://localhost:8000/docs**.

### Terminal 2 — Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

`frontend/.env.local` already points at the backend (`NEXT_PUBLIC_API_URL=http://localhost:8000`, `NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/queue`) — no edits needed for local dev.

The app is now live at **http://localhost:3000**. Start with the Command Center at `/command-center`.

> Start the backend first — the frontend's WebSocket connection and data fetches will fail (and pages will look empty) until `http://localhost:8000` is reachable.

### Resetting / re-seeding data

```bash
cd backend
python scripts/reset_database.py   # wipes all tables AND re-seeds in one step
```

Or just `python scripts/seed_database.py` on its own if the database is already empty.

### Running backend tests

```bash
cd backend
pytest -q
```

31 tests cover the individual engines (`test_risk_engine.py`, `test_safety_engine.py`, `test_confidence_engine.py`, `test_deterioration_engine.py`) plus API and end-to-end integration (`test_api.py`, `test_integration.py`).

---

## Architecture

**Backend** (`backend/app/`)
- `engines/` — the 9 deterministic/LLM-assisted decision engines: `safety_engine`, `risk_engine`, `confidence_engine`, `decision_engine`, `deterioration_engine`, `alert_engine`, `capacity_engine`, `queue_engine`, `recommendation_engine`.
- `api/` — FastAPI routers: `/patients`, `/triage`, `/queue`, `/alerts`, `/capacity`, `/simulate`, `/override`, `/audit`.
- `services/` — business logic between the API layer and the engines/DB, plus `llm_service.py` (Hugging Face `Qwen/Qwen2.5-*-Instruct` explanation layer).
- `models/` / `schemas/` — SQLAlchemy models and Pydantic request/response schemas.
- `realtime/` — WebSocket manager broadcasting queue/alert/capacity updates to connected clients.

**Frontend** (`frontend/`)
- `app/` — Next.js App Router pages: `dashboard`, `command-center`, `queue`, `patients`, `triage`, `capacity`, `alerts`, `audit`, `surge`.
- `hooks/` — data-fetching hooks (`useQueue`, `useAlerts`, `useCapacity`, `usePatients`, `useWebSocket`, ...).
- `lib/api.ts` — typed client for every backend endpoint.
- `components/` — shared UI (queue items, priority badges, layout shell).

### Key API endpoints

| Area | Endpoint | Purpose |
|---|---|---|
| Triage | `POST /triage/assess` | Run a new patient through the engine pipeline |
| Queue | `GET /queue` | Live-ranked priority queue |
| Patients | `GET /patients/{id}` | Full patient detail incl. latest assessment/vitals |
| Patients | `PATCH /patients/{id}/status` | Change status directly (e.g. mark treated → removes from queue, even with no bed) |
| Capacity | `GET /capacity` | Beds, staff/equipment, occupancy, reallocation recommendations |
| Capacity | `POST /capacity/beds` / `DELETE /capacity/beds/{id}` | Add / remove individual beds |
| Capacity | `PUT /capacity/beds/totals` | Set General/ICU bed counts in one call (reconciles by adding/removing empty beds) |
| Capacity | `POST /capacity/beds/allocate` / `/release` / `/reallocate` | Bed assignment workflow |
| Override | `POST /override` | Clinician priority override (human-in-the-loop) |
| Audit | `GET /audit` | Full audit trail of engine decisions and clinician actions |

Full interactive reference: `http://localhost:8000/docs` once the backend is running.

---

## Troubleshooting

- **Frontend loads but shows no data / "Failed to fetch"** — backend isn't running, or started on a different port than `NEXT_PUBLIC_API_URL` in `frontend/.env.local`.
- **`ModuleNotFoundError` on backend start** — the virtual environment isn't activated, or `pip install -r requirements.txt` didn't complete; re-run both.
- **Empty queue after seeding** — check the backend terminal output for errors during `seed_database.py`; if the DB already had data, run `python scripts/reset_database.py` instead (wipes + re-seeds in one step).
- **Port already in use** — change `--port 8000` on the `uvicorn` command and update `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_WS_URL` to match.
