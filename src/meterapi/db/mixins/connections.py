from sqlmodel import select

from meterapi.db.mixins.base import _RepoBase
from meterapi.models import Connection


class ConnectionMixin(_RepoBase):
    def list_connections_for_complex(
        self, c_id: int, *, limit: int, offset: int,
    ) -> list[Connection]:
        stmt = (
            select(Connection)
            .where(Connection.complex_id == c_id)
            .order_by(Connection.c_id)
            .limit(limit).offset(offset)
        )
        return list(self.session.exec(stmt).all())

    def get_connection(self, c_id: int) -> Connection | None:
        return self.session.get(Connection, c_id)
