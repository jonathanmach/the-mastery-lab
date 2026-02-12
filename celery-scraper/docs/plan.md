# Celery Scraper — Minimum Learning Project



## Context

Create a standalone Celery learning project that demonstrates core task queue concepts through a practical use case: scraping Hacker News top stories via their public JSON API. The project includes a FastAPI layer to trigger tasks and view results, Celery Beat for periodic scheduling, and covers progressively complex patterns (simple tasks → retries → chains → groups → chords).

## Project Structure

```
celery-scraper/
├── pyproject.toml              # uv + hatchling, deps, ruff config
├── .python-version             # 3.12
├── .gitignore
├── .env.example
├── docker-compose.yml          # Redis only
├── README.md
├── docs/
│   └── plan.md                 # Project design doc (this plan)
├── src/app/
│   ├── __init__.py
│   ├── config.py               # Pydantic Settings (Redis, HN API, Beat interval)
│   ├── celery_app.py           # Celery app factory + config with concept comments
│   ├── beat_schedule.py        # Beat schedule definition
│   ├── tasks/
│   │   ├── __init__.py         # Re-exports for autodiscover
│   │   ├── fetch.py            # fetch_top_stories, fetch_story_details (retries)
│   │   ├── process.py          # process_stories (filter/sort — chain step)
│   │   ├── store.py            # store_results (JSON file persistence)
│   │   └── pipelines.py        # run_scrape_pipeline (chord/group orchestration)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app
│   │   ├── routes.py           # POST /scrape, GET /tasks/{id}, GET /results
│   │   └── schemas.py          # Pydantic request/response models
│   └── storage/
│       ├── __init__.py
│       └── json_store.py       # Read/list JSON result files
└── tests/
    ├── conftest.py             # task_always_eager fixture
    ├── test_tasks/
    │   ├── test_fetch.py
    │   └── test_process.py
    └── test_api/
        └── test_routes.py
```

## Celery Concepts Covered

| Concept | Where |
|---|---|
| App creation & configuration | `celery_app.py` |
| Simple task (`@celery.task`) | `tasks/fetch.py` → `fetch_top_stories` |
| `bind=True` + `self` access | `tasks/fetch.py` → `fetch_story_details` |
| Retry with exponential backoff | `tasks/fetch.py` → `autoretry_for`, `retry_backoff` |
| Task as chain step | `tasks/process.py` → receives previous task's output |
| `group()` — parallel execution | `tasks/pipelines.py` |
| `chord()` — group + callback | `tasks/pipelines.py` |
| `chain()` / pipe operator | `tasks/pipelines.py` → `process.s() \| store.s()` |
| `.s()` signatures | `tasks/pipelines.py` |
| Celery Beat scheduling | `beat_schedule.py` |
| `.delay()` / `.apply_async()` | `api/routes.py` |
| `AsyncResult` status polling | `api/routes.py` |
| `task_always_eager` for tests | `tests/conftest.py` |
| `autodiscover_tasks` | `celery_app.py` |

## Key Design Decisions

- **JSON file storage** (not SQLite) — keeps focus on Celery, not ORMs. Files are inspectable.
- **`httpx`** over `requests` — already ships with `fastapi[standard]`, avoids extra dependency.
- **Celery instance named `celery`** (not `app`) — avoids confusion with FastAPI's `app`. CLI becomes `celery -A app.celery_app:celery worker`.
- **`run_scrape_pipeline` calls `fetch_top_stories()` directly** (not `.delay()`) — it's already inside a worker; calling directly gives us the IDs to build the chord.
- **`periodic_pipeline` is a thin wrapper** — Beat gets a simple launcher; the real orchestration is in `run_scrape_pipeline` so it's callable from both Beat and the API.

## Dependencies

```
celery[redis]>=5.4.0       # Task queue + Redis broker/backend
fastapi[standard]>=0.115.12 # API layer (includes uvicorn, httpx)
httpx>=0.28.0              # HTTP client for HN API calls
pydantic-settings>=2.9.0  # Env-based config

# Dev
pytest, ruff, python-dotenv, flower
```

## Implementation Order

1. **Scaffolding** — `pyproject.toml`, `.python-version`, `.gitignore`, `.env.example`, `docker-compose.yml`
2. **Config** — `src/app/__init__.py`, `config.py`
3. **Celery app** — `celery_app.py`, `beat_schedule.py`
4. **Tasks** — `fetch.py` → `process.py` → `store.py` → `pipelines.py` (+ `tasks/__init__.py`)
5. **Storage helpers** — `storage/__init__.py`, `json_store.py`
6. **API layer** — `schemas.py` → `routes.py` → `main.py` (+ `api/__init__.py`)
7. **Tests** — `conftest.py`, `test_fetch.py`, `test_process.py`, `test_routes.py`
8. **Docs** — Save this plan to `docs/plan.md`
9. **README** — How to run, concept map

## Verification

1. `uv sync` — dependencies install cleanly
2. `docker compose up -d` — Redis starts
3. Start worker: `uv run celery -A app.celery_app:celery worker --loglevel=info`
4. Start Beat: `uv run celery -A app.celery_app:celery beat --loglevel=info`
5. Start API: `uv run fastapi dev src/app/api/main.py`
6. Trigger scrape: `curl -X POST http://localhost:8000/api/scrape -H "Content-Type: application/json" -d '{"limit": 10}'`
7. Check task: `curl http://localhost:8000/api/tasks/<task_id>`
8. View results: `curl http://localhost:8000/api/results/latest`
9. `uv run pytest` — all tests pass
