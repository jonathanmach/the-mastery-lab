# Celery Scraper — HN Top Stories

Learning project: Celery task queue with FastAPI and Hacker News API.

Demonstrates core Celery concepts through a practical web scraping pipeline that fetches, processes, and stores Hacker News top stories.

## Celery Concepts Covered

| Concept | File |
|---|---|
| App creation & config | `src/app/celery_app.py` |
| Simple task | `src/app/tasks/fetch.py` → `fetch_top_stories` |
| `bind=True` + retries | `src/app/tasks/fetch.py` → `fetch_story_details` |
| Task chaining (pipe `\|`) | `src/app/tasks/pipelines.py` |
| `group()` — parallel tasks | `src/app/tasks/pipelines.py` |
| `chord()` — group + callback | `src/app/tasks/pipelines.py` |
| `.s()` signatures | `src/app/tasks/pipelines.py` |
| Celery Beat scheduling | `src/app/beat_schedule.py` |
| `.delay()` + `AsyncResult` | `src/app/api/routes.py` |
| `task_always_eager` testing | `tests/conftest.py` |

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker

## Setup

```bash
cd celery-scraper
cp .env.example .env
uv sync
```

## Running

### 1. Start Redis

```bash
docker compose up -d
```

### 2. Start the Celery Worker (Terminal 1)

```bash
uv run celery -A app.celery_app:celery worker --loglevel=info
```

### 3. Start Celery Beat (Terminal 2)

```bash
uv run celery -A app.celery_app:celery beat --loglevel=info
```

### 4. Start FastAPI (Terminal 3)

```bash
uv run fastapi dev src/app/api/main.py
```

### 5. (Optional) Start Flower — Celery monitoring UI (Terminal 4)

```bash
uv run celery -A app.celery_app:celery flower --port=5555
```

Then open http://localhost:5555.

## Try It Out

```bash
# Trigger a scrape
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "min_score": 5}'

# Check task status (use the task_id from the response above)
curl http://localhost:8000/api/tasks/<task_id>

# View latest results
curl http://localhost:8000/api/results/latest

# List all result files
curl http://localhost:8000/api/results
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/scrape` | Trigger a scrape pipeline |
| `GET` | `/api/tasks/{task_id}` | Check task status |
| `GET` | `/api/results` | List stored result files |
| `GET` | `/api/results/latest` | Get most recent results |
| `GET` | `/api/results/{filename}` | Get specific result file |
| `GET` | `/health` | Health check |

## Running Tests

```bash
uv run pytest
```

Tests run with `task_always_eager=True` — no Redis needed.

## Architecture

```
[FastAPI] --POST /scrape--> [Redis Broker] --> [Celery Worker]
                                                    |
                                            run_scrape_pipeline
                                                    |
                                        1. fetch_top_stories()
                                        2. chord:
                                           group(fetch_story_details x N)
                                             |
                                           process_stories
                                             |
                                           store_results -> data/*.json

[Celery Beat] --every 5min--> periodic_pipeline --> run_scrape_pipeline
```
