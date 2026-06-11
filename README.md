# meterapi

FastAPI service that returns the latest energy-meter readings from the Postgres warehouse.

## Layout

- `src/meterapi/models/` — SQLModel ORM tables (`db.py`) and Pydantic API schemas (`api.py`). API schemas extend `ApiModel` (camelCase JSON, `from_attributes`). Everything is re-exported from the package root.
- `src/meterapi/db/` — `Repository` (composed from per-resource mixins in `db/mixins/`) plus the session/engine factory. Query methods accept primitive arguments (no request shapes).
- `src/meterapi/app/` — FastAPI app (`main.py`), routers (`routers/`), global exception handlers (`errors.py`), and shared helpers (`_responses.py`, `_time.py`).

## Endpoints

Infra (unversioned):

- `GET /health` — process liveness; does **not** touch the database.
- `GET /ready` — readiness; returns `503` when the database is unreachable.

Data API (all under `/v1`, paginated list responses use the `Page` envelope):

- `GET /v1/complexes` — list complexes.
- `GET /v1/complexes/{complex_id}/connections` — connections for a complex.
- `GET /v1/complexes/{complex_id}/meters` — active meters for a complex.
- `GET /v1/connections/{connection_id}/rooms` — rooms for a connection.
- `GET /v1/meters/stale?hours={1..8760}` — meters with no recent readings.
- `GET /v1/meters/{serial_number}` — meter detail incl. last reading.
- `GET /v1/measurements?serial_number={str}&from={iso}&to={iso}&measurement_type={str}` — raw measurements.
- `GET /v1/measurements/aggregate?serial_number={str}&grain={day|month}&from={iso}&to={iso}` — bucketed aggregates.

## API conventions

- **Versioning**: data endpoints live under `/v1`. Infra probes (`/health`, `/ready`) are unversioned.
- **JSON casing**: response bodies are **camelCase** (e.g. `dueDate`, `serialNumber`, `complexId`). A resource's own primary key is `id`; foreign keys are qualified (`complexId`, `connectionId`).
- **Path & query params**: **snake_case** (`/v1/complexes/{complex_id}`, `?serial_number=...`).
- **Pagination**: list endpoints return `{ "items": [...], "total": <int>, "limit": <int>, "offset": <int> }`. `limit` is `1..500` (default 100), `offset` `>= 0` (default 0).
- **Time windows**: `from`/`to` are ISO-8601, interpreted as the half-open interval `[from, to)`. Naive datetimes are assumed UTC. Defaults: `to = now`, `from = now - 7d`. `from > to` yields `400`.
- **Errors**: error bodies are `{ "detail": <string> }`. `404` for missing resources, `400` for bad ranges, `422` for request validation (FastAPI's native shape), `503` when the database is unreachable.

## Configuration

DB credentials are pulled from AWS Secrets Manager at startup:

- `DB_SECRET_ARN` — ARN of the secret holding `{username, password, host, port, dbname}`.
- `AWS_REGION` — defaults to `eu-central-1`.

## Run

```bash
uv sync
uv run uvicorn meterapi.app.main:app --reload
```

## Docker (local or AWS App Runner)

Build and run locally (defaults to port **8000**):

```bash
docker build -t meterapi .
docker run --rm -p 8000:8000 --env-file .env meterapi
```

App Runner injects **`PORT`**; the image listens on `0.0.0.0` and uses `${PORT:-8000}`. For an `linux/amd64` service from an Apple Silicon machine:

```bash
docker build --platform linux/amd64 -t meterapi .
```

Configure the service health check to hit **`/health`** (or a dedicated liveness path your team prefers).
