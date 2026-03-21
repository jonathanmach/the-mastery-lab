# FHIR Platform Prototype

AWS-first FHIR R4 healthcare data platform prototype using HAPI FHIR (self-hosted), OpenSearch, FastAPI, and Vue.js.

## Quick Start

### 1. Start local services

```bash
docker compose up -d
```

Wait for HAPI FHIR (`:8080`) and OpenSearch (`:9200`) to be healthy.

### 2. Install Python dependencies

```bash
uv sync
```

### 3. Generate Synthea patient data

Download Synthea and generate bundles:

```bash
# Download synthea JAR (one-time)
curl -L https://github.com/synthetichealth/synthea/releases/latest/download/synthea-with-dependencies.jar \
     -o synthea-with-dependencies.jar

# Generate 50 patients
java -jar synthea-with-dependencies.jar -p 50 --exporter.fhir.export true \
     --exporter.baseDirectory ./data
mv ./data/fhir/*.json ./data/synthea_bundles/
```

### 4. Ingest bundles

```bash
cp .env.example .env
uv run python scripts/ingest_bundles.py
```

### 5. Start the API

```bash
uv run fastapi dev src/app/api/main.py
```

API docs: http://localhost:8000/docs

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Architecture

```
Synthea JSON (local files)
        ↓
  ingest_bundles.py
        ↓
  HAPI FHIR (Docker :8080)  ←→  FastAPI BFF (:8000)
        ↓                               ↑
  OpenSearch (:9200)         ←→  Vue.js frontend (:5173)
```

## Running tests

```bash
uv run pytest tests/ -v
```

## Project structure

```
src/app/
  config.py               pydantic-settings
  dependencies.py         FastAPI DI
  db/                     SQLAlchemy ImportRecord
  ingestion/              source_reader, bundle_parser, fhir_client, import_tracker
  projection/             search_projector (OpenSearch index)
  api/                    FastAPI routes + schemas
scripts/
  ingest_bundles.py       CLI ingestion tool
tests/                    pytest suite
frontend/                 Vue 3 + Vite
```
