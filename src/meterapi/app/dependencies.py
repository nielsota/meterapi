from fastapi import Depends
from sqlmodel import Session

from meterapi.db import Repository, get_session


def get_repository(session: Session = Depends(get_session)) -> Repository:
    return Repository(session)
