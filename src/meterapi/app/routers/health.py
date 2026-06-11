from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlmodel import Session

from meterapi.app._responses import SERVICE_UNAVAILABLE
from meterapi.db import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Process liveness — does not touch the database."""
    return {"status": "ok"}


@router.get("/ready", responses=SERVICE_UNAVAILABLE)
def ready(session: Session = Depends(get_session)) -> dict[str, str]:
    """Readiness — verifies the database is reachable."""
    try:
        session.exec(text("SELECT 1")).one()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="db_unreachable") from exc
    return {"status": "ready"}
