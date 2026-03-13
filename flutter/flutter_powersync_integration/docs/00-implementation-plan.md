# PowerSync + Flutter Prototype: Implementation Plan

## Context

Learning prototype for integrating Flutter with PowerSync. A clean Flutter scaffold exists at `powersync_experiment/`. We need to build the full stack: Docker infrastructure (Postgres + PowerSync service + FastAPI backend) and wire up the Flutter app with PowerSync SDK.

**Decisions**: Python/FastAPI backend, PostgreSQL for bucket storage (no MongoDB), simple todo list domain.

---

## File Tree (new files to create)

```
docker-compose.yml
db/
  init.sql
config/
  powersync.yaml
  sync_rules.yaml
backend/
  Dockerfile
  requirements.txt
  app/
    __init__.py
    main.py
    auth.py
    crud.py
    db.py
docs/
  00-implementation-plan.md          # Copy of this plan (user requested)
powersync_experiment/
  lib/
    models/schema.dart               # PowerSync client-side schema
    powersync/backend_connector.dart  # BackendConnector implementation
    powersync/powersync.dart          # DB init + connect
    main.dart                         # Updated: todo list UI
```

---

## Step 1: Docker Infrastructure

### 1.1 `docker-compose.yml` (project root)

3 services on default network:

| Service | Image | Ports | Key Config |
|---|---|---|---|
| `pg-db` | `postgres:16` | 5432:5432 | `wal_level=logical` via command override, mounts `db/init.sql` |
| `powersync` | `journeyapps/powersync-service:latest` | 8080:8080 | Mounts `config/`, depends on pg-db healthy |
| `backend` | Build from `./backend` | 6060:6060 | `DATABASE_URL` env var, depends on pg-db healthy |

### 1.2 `db/init.sql`

- Create `lists` and `todos` tables with `TEXT` primary keys (PowerSync requires text IDs)
- Default UUIDs via `uuid_generate_v4()::text`
- `CREATE PUBLICATION powersync FOR TABLE lists, todos;`

### 1.3 `config/powersync.yaml`

- Replication source: `postgresql://postgres:postgres@pg-db:5432/powersync_todo`
- **Bucket storage**: `type: postgresql` (same Postgres instance, OK for Postgres 16)
- Auth: JWKS from `http://backend:6060/api/auth/keys`, audience `powersync-dev`
- Sync rules path: `sync_rules.yaml`

### 1.4 `config/sync_rules.yaml`

Global bucket (syncs everything to all clients):
```yaml
bucket_definitions:
  global:
    data:
      - SELECT * FROM lists
      - SELECT * FROM todos
```

### 1.5 Backend (`backend/`)

**Auth (`auth.py`)**:
- Generate RSA key pair at startup (in-memory, dev-only)
- `POST /api/auth/token` — accepts `{"user_id": "..."}`, returns JWT (RS256, exp=55min, aud=powersync-dev)
- `GET /api/auth/keys` — returns JWKS with the RSA public key

**CRUD (`crud.py`)**:
- `PUT /api/data/{table}/{id}` — upsert (INSERT ... ON CONFLICT DO UPDATE)
- `PATCH /api/data/{table}/{id}` — partial update
- `DELETE /api/data/{table}/{id}` — delete
- Validate `table` against allowlist `{"lists", "todos"}`

**DB (`db.py`)**: psycopg2 connection factory using `DATABASE_URL` env var.

---

## Step 2: Flutter App Integration

### 2.1 Dependencies (`pubspec.yaml`)

Add: `powersync`, `path_provider`, `path`, `http`, `uuid`

### 2.2 macOS Entitlements

Add `com.apple.security.network.client` to both `DebugProfile.entitlements` and `Release.entitlements` (required for outbound HTTP).

### 2.3 `lib/models/schema.dart`

PowerSync schema matching Postgres tables. No `id` column (auto-created). `completed` as `Column.integer()` (SQLite has no bool).

### 2.4 `lib/powersync/backend_connector.dart`

- `fetchCredentials()`: POST to `localhost:6060/api/auth/token`, return `PowerSyncCredentials`
- `uploadData()`: Loop `getCrudBatch()`, map each `CrudEntry` to PUT/PATCH/DELETE on the backend API

### 2.5 `lib/powersync/powersync.dart`

Initialize `PowerSyncDatabase` with schema + path, call `db.connect(connector:)`.

### 2.6 `lib/main.dart`

Simple todo list UI:
- Create a default list on init
- `db.watch()` with StreamBuilder for reactive todo list
- Add/toggle/delete todos via local `db.execute()` (instant, synced automatically)

---

## Step 3: Verification

1. `docker compose up --build` — wait for all services healthy
2. Test backend independently:
   ```bash
   curl -X POST http://localhost:6060/api/auth/token -H "Content-Type: application/json" -d '{"user_id":"user1"}'
   curl http://localhost:6060/api/auth/keys
   ```
3. `cd powersync_experiment && flutter run -d macos`
4. Add a todo in the app, verify it appears in Postgres:
   ```bash
   docker compose exec pg-db psql -U postgres -d powersync_todo -c "SELECT * FROM todos;"
   ```
5. Insert a row directly in Postgres, verify it appears in the Flutter app within seconds

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Text IDs in Postgres | PowerSync client-side SQLite uses text IDs |
| RSA keys in-memory at startup | Dev-only simplicity |
| JWT expiry = 55 min | PowerSync rejects tokens >= 60 min |
| Global sync bucket | No per-user filtering needed for prototype |
| Same Postgres for source + bucket storage | OK for Postgres >= 14; simplest setup |
| `Column.integer('completed')` | SQLite has no boolean type |

## Pitfalls to Watch

1. If Postgres data volume exists from a prior run without `wal_level=logical`, need `docker compose down -v`
2. Flutter on macOS needs `network.client` entitlement or HTTP calls silently fail
3. Publication must include all tables referenced in sync rules
4. Flutter app uses `localhost` ports — won't work on physical devices (use host IP instead)
