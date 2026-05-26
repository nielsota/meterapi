from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlmodel import Session

from meterapi.db import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
def health(session: Session = Depends(get_session)) -> dict[str, str]:
    try:
        session.exec(text("SELECT 1")).one()
    except Exception:
        raise HTTPException(status_code=503, detail="db_unreachable")
    return {"status": "ok"}
