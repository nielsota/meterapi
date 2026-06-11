from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import func, literal
from sqlmodel import select

from meterapi.db.mixins.base import _RepoBase
from meterapi.models import EnergyMeasurement

Grain = Literal["day", "month"]


@dataclass(frozen=True, slots=True)
class AggregateRow:
    bucket: datetime
    sum: float
    avg: float
    count: int


class MeasurementMixin(_RepoBase):
    def list_measurements(
        self, *, serial: str, from_: datetime, to: datetime,
        measurement_type: str | None, limit: int, offset: int,
    ) -> list[EnergyMeasurement]:
        stmt = select(EnergyMeasurement).where(
            EnergyMeasurement.serial_number == serial,
            EnergyMeasurement.value_time >= from_,
            EnergyMeasurement.value_time < to,
        )
        if measurement_type is not None:
            stmt = stmt.where(EnergyMeasurement.measurement_type == measurement_type)
        stmt = (
            stmt.order_by(
                EnergyMeasurement.value_time.desc(),
                EnergyMeasurement.energy_measurement_id.desc(),
            )
            .limit(limit).offset(offset)
        )
        return list(self.session.exec(stmt).all())

    def count_measurements(
        self, *, serial: str, from_: datetime, to: datetime,
        measurement_type: str | None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(EnergyMeasurement)
            .where(
                EnergyMeasurement.serial_number == serial,
                EnergyMeasurement.value_time >= from_,
                EnergyMeasurement.value_time < to,
            )
        )
        if measurement_type is not None:
            stmt = stmt.where(EnergyMeasurement.measurement_type == measurement_type)
        return self.session.exec(stmt).one()

    def aggregate_measurements(
        self, *, serial: str, grain: Grain,
        from_: datetime, to: datetime, measurement_type: str | None,
    ) -> list[AggregateRow]:
        if grain not in ("day", "month"):
            raise ValueError(f"invalid grain: {grain}")
        bucket = func.date_trunc(literal(grain), EnergyMeasurement.value_time).label("bucket")
        stmt = select(
            bucket,
            func.sum(EnergyMeasurement.value).label("sum"),
            func.avg(EnergyMeasurement.value).label("avg"),
            func.count().label("count"),
        ).where(
            EnergyMeasurement.serial_number == serial,
            EnergyMeasurement.value_time >= from_,
            EnergyMeasurement.value_time < to,
        )
        if measurement_type is not None:
            stmt = stmt.where(EnergyMeasurement.measurement_type == measurement_type)
        stmt = stmt.group_by(bucket).order_by(bucket)
        rows = self.session.exec(stmt).all()
        return [
            AggregateRow(bucket=r[0], sum=float(r[1]), avg=float(r[2]), count=int(r[3]))
            for r in rows
        ]
