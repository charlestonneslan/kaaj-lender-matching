# Kaaj Lender Matching Platform

A loan underwriting + lender matching system for equipment finance. Takes a
business loan application, evaluates it against 5 real lenders' credit
policies, returns ranked matches with per-rule pass/fail explanations.

## Quickstart

### With Docker

```sh
docker compose up --build
```

Brings up Postgres on `:5432`, FastAPI on `:8000`, React/Vite on `:5173`. The
backend auto-seeds the 5 lenders from `backend/lenders/*.yaml` on first boot.

### Without Docker (sqlite fallback)

Useful if your Docker Desktop is acting up. Backend defaults to Postgres but
runs cleanly against sqlite when you pass `DATABASE_URL`:

```sh
# backend (terminal 1)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
DATABASE_URL=sqlite:///./kaaj.db python -m app.seed
DATABASE_URL=sqlite:///./kaaj.db uvicorn app.main:app --reload --port 8000

# frontend (terminal 2)
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173, click **New Application**, hit submit. You
get a ranked list of lender matches with per-rule pass/fail reasons.

Run the tests:
```sh
cd backend && pytest
```

## What's in the box

- 5 lenders modeled from their actual policy PDFs (in `backend/lenders/_pdfs/`)
- Rule engine that handles numeric, set-membership, boolean, and composite
  rules with weighted fit scoring
- Three-section app: applications list/form/detail, lender browser, rule editor
- 17 backend tests covering the engine + cross-lender matching

## Architecture

```
backend/
  app/
    matching/        rule engine (rules.py, engine.py)
    models/          SQLModel tables
    schemas/         Pydantic I/O
    api/             FastAPI routers
    seed.py          YAML to DB upsert
  lenders/           one YAML per lender (versioned, source of truth)
    _pdfs/           original policy PDFs
  tests/

frontend/
  src/
    api/             typed fetch wrapper
    pages/           applications + lenders screens
    types.ts         shared types
```

### The rule engine

Each lender has one or more **programs** (tiers, rate bands, sub-programs).
Each program has a list of **rules**. A rule is one of:

- `numeric` (FICO >= 700, amount between $10K and $75K)
- `set` (state not in {CA, NV}, industry not in {cannabis, gaming})
- `boolean` (is_us_citizen == true)
- `composite` (registered Python function for things that don't fit, e.g.
  Stearns's revolver-utilization rule)

Each rule has a `weight` and a `hard` flag. Hard failures disqualify the
program. Soft failures only dock the fit score:

```
fit_score = (sum of weights for passed rules / total weight) * 100
```

For each lender, the engine picks the best-scoring **eligible** program, or
falls back to the highest-scoring program with reasons if nothing's eligible.
Results are ranked across lenders.

### Adding a new lender

1. Drop the PDF in `backend/lenders/_pdfs/`
2. Create `backend/lenders/<slug>.yaml` (see existing ones as templates)
3. `python -m app.seed` (or just restart the backend; seed runs on startup)
4. The lender appears in the UI; rules editable from `/lenders/<id>`

The YAML is the source of truth in git. UI edits write to the DB. Re-running
the seed is idempotent (delete + recreate programs/rules).

## API

OpenAPI docs at http://localhost:8000/docs once it's running.

| Method | Path | Purpose |
|---|---|---|
| GET | `/applications` | list applications |
| POST | `/applications` | create new application |
| GET | `/applications/{id}` | get one |
| PUT | `/applications/{id}` | update all sections |
| DELETE | `/applications/{id}` | remove |
| POST | `/applications/{id}/evaluate` | start an underwriting run (async, parallel per-lender) |
| GET | `/applications/{id}/results` | get the last ranked results |
| GET | `/applications/{id}/runs` | history of underwriting runs for this app |
| GET | `/applications/runs/{run_id}` | run status (pending / running / completed / failed) |
| GET | `/lenders` | list lenders + programs + rules |
| GET | `/lenders/{id}` | get one |
| POST | `/lenders` | create a new lender |
| POST | `/lenders/{id}/programs` | add a program to a lender |
| POST | `/lenders/programs/{program_id}/rules` | add a rule |
| PATCH | `/lenders/rules/{rule_id}` | edit a rule |
| DELETE | `/lenders/rules/{rule_id}` | remove a rule |
| GET | `/healthz` | liveness |

### The underwriting run

`POST /applications/{id}/evaluate` does two things: creates an
`UnderwritingRun` row to track status, then fans out per-lender evaluation
across `asyncio.gather` so the run completes in roughly the slowest
single lender's time, not the sum. Each per-lender evaluation goes
through an exponential-backoff retry (3 attempts) so a transient failure
in one lender's evaluation doesn't kill the whole run. Progress is
persisted (`lenders_done` ticks up as each lender finishes) and the
run history is queryable.

In production this is the shape a Hatchet workflow would orchestrate
across worker pods: one fan-out task per lender, a join step, with
Hatchet's retry policy instead of the inline decorator.

## Development

```sh
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest

# frontend
cd frontend
npm install
npm run dev
```

For the backend to connect to a local Postgres outside Docker, set
`DATABASE_URL=postgresql+psycopg://kaaj:kaaj@localhost:5432/kaaj` and run
`uvicorn app.main:app --reload`.

## Tech stack

Python 3.12, FastAPI, SQLModel, Pydantic v2, Postgres 16. React 18, TypeScript,
TanStack Query, Tailwind, Vite.
