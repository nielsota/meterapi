from sqlmodel import select

from meterapi.db.mixins.base import _RepoBase
from meterapi.models import Complex


class ComplexMixin(_RepoBase):
    def list_complexes(self, *, limit: int, offset: int) -> list[Complex]:
        stmt = select(Complex).order_by(Complex.c_id).limit(limit).offset(offset)
        return list(self.session.exec(stmt).all())

    def get_complex(self, c_id: int) -> Complex | None:
        return self.session.get(Complex, c_id)
