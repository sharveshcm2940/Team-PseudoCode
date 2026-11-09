# PALS — Personalised Adaptive Learning System

PALS is a research-oriented DSA learning platform with a React student workspace and a modular FastAPI backend. Correctness comes from Judge0, concept mastery from Bayesian Knowledge Tracing (BKT), and teaching support from an auditable diagnosis/intervention pipeline. Ollama is used only to phrase tutoring responses.

## Quick start

1. Optionally copy `.env.example` to `.env` and start with `PALS_ENV_FILE=.env docker compose up --build` when custom settings are needed.
2. Otherwise run `docker compose up --build` with the safe development defaults.
3. Open `http://localhost:5173`; API documentation is at `http://localhost:8000/docs`.

For local development:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend && alembic upgrade head && uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend && npm install && npm run dev
```

The app seeds its data-driven curriculum on first startup. Judge0 and Ollama URLs/model names are environment-configured. The development default targets the locally installed `qwen3:4b-q4_K_M` model. If Ollama is unavailable, tutor endpoints return deterministic, scaffold-appropriate fallback guidance. Judge0 failure is reported explicitly and is never replaced by a fake result.

## Architecture

- `backend/app/api`: versioned HTTP contracts
- `backend/app/models.py`: persistent learning graph
- `backend/app/services`: execution, BKT, diagnosis, interventions, tutoring
- `backend/app/data/curriculum.json`: extensible curriculum source
- `frontend/src`: responsive learning workspace and analytics
- `backend/tests`: mathematical, policy, and API coverage

Hidden cases live only in the database and are excluded from problem responses. A submission lifecycle is persisted as `CREATED → QUEUED → RUNNING → EVALUATED → COMPLETED/FAILED`. Only completed Judge0 results update mastery.
