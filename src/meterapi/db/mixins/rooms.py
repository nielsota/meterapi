from sqlalchemy import func
from sqlmodel import select

from meterapi.db.mixins.base import _RepoBase
from meterapi.models import Room


class RoomMixin(_RepoBase):
    def list_rooms_for_connection(
        self, connection_id: int, *, limit: int, offset: int,
    ) -> list[Room]:
        stmt = (
            select(Room)
            .where(Room.connection_id == connection_id)
            .order_by(Room.r_id)
            .limit(limit).offset(offset)
        )
        return list(self.session.exec(stmt).all())

    def count_rooms_for_connection(self, connection_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Room)
            .where(Room.connection_id == connection_id)
        )
        return self.session.exec(stmt).one()
