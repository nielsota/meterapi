# meterapi

FastAPI service that returns the latest energy-meter readings from the Postgres warehouse.

## Layout

- `src/meterapi/models/` — SQLModel ORM tables (`db.py`), Pydantic API schemas (`api.py`), and the DB session factory. Everything is re-exported from the package root.
- `src/meterapi/services/dbservice.py` — `MeterRepository`, the database-operations class. Takes a `Session` and exposes query methods that accept primitive arguments (no request shapes).
- `src/meterapi/app/main.py` — FastAPI app, routes, and the `MeterRepository` dependency.

## Endpoints

- `GET /health` — liveness probe.
- `GET /meters/last-values?connectionId={int}&meterType={str}` — most recent value per meter for a given connection and installation goal (e.g. `WKV`, `WARM`, `KOUD`).

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
