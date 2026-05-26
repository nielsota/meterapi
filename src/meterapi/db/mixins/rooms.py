from sqlmodel import select

from meterapi.db.mixins.base import _RepoBase
from meterapi.models import Room


class RoomMixin(_RepoBase):
    def list_rooms_for_connection(
        self, c_id: int, *, limit: int, offset: int,
    ) -> list[Room]:
        stmt = (
            select(Room)
            .where(Room.connection_id == c_id)
            .order_by(Room.r_id)
            .limit(limit).offset(offset)
        )
        return list(self.session.exec(stmt).all())
