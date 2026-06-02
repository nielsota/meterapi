from meterapi.db.mixins.base import _RepoBase
from meterapi.db.mixins.complexes import ComplexMixin
from meterapi.db.mixins.connections import ConnectionMixin
from meterapi.db.mixins.measurements import MeasurementMixin
from meterapi.db.mixins.meters import MeterMixin
from meterapi.db.mixins.rooms import RoomMixin


class Repository(
    ComplexMixin,
    ConnectionMixin,
    MeterMixin,
    MeasurementMixin,
    RoomMixin,
    _RepoBase,
):
    pass


__all__ = ["Repository"]
