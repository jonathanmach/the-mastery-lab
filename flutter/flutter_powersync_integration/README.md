# Flutter + PowerSync Integration

Learning prototype for integrating a Flutter app with [PowerSync](https://www.powersync.com/) for offline-first, real-time data sync.

The stack is: Flutter (macOS) + PowerSync service + FastAPI backend + PostgreSQL. The domain is a simple todo list.

## Experimentation log

#### `@2025-03-13`: Full stack integration — Flutter ↔ PowerSync ↔ FastAPI ↔ Postgres

![Custom Badge](https://img.shields.io/badge/Outcome-✅_Success-brightgreen)

Built the full stack from scratch:
- Docker Compose wires up Postgres (with `wal_level=logical`), the PowerSync service, and a FastAPI backend.
- PowerSync bucket storage runs on the same Postgres instance (no MongoDB needed, requires Postgres >= 14).
- FastAPI backend generates an RSA key pair at startup and issues short-lived JWTs (RS256, 55-min expiry) — PowerSync rejects tokens >= 60 min.
- Flutter app uses `PowerSyncDatabase` with a `BackendConnector` that fetches credentials and uploads CRUD mutations to the backend.
- Reactive UI via `db.watch()` + `StreamBuilder` — local writes appear instantly, sync happens in the background.

Key pitfalls encountered:
- SQLite has no boolean type — `completed` is `Column.integer()` on the client, the backend must coerce `0`/`1` → `bool` before inserting into Postgres.
- macOS Flutter requires `com.apple.security.network.client` in both `DebugProfile.entitlements` and `Release.entitlements` for outbound HTTP.
- Postgres data volume from a prior run without `wal_level=logical` will silently break replication — requires `docker-compose down -v`.
- PowerSync caches the JWKS; if the backend container is rebuilt (new in-memory RSA keys), PowerSync gets 401s briefly until it re-fetches. Self-heals within seconds.

See [docs/00-implementation-plan.md](docs/00-implementation-plan.md) for the full design.

## Running locally

```bash
# Start the backend infrastructure
docker-compose up --build

# Run the Flutter app (macOS)
cd powersync_experiment && flutter run -d macos
```

## Resources

- [PowerSync documentation](https://docs.powersync.com/)
- [PowerSync Flutter SDK](https://pub.dev/packages/powersync)
- [PowerSync sync rules reference](https://docs.powersync.com/usage/sync-rules)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
