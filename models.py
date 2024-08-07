from sqlalchemy import String, Integer, REAL, TIMESTAMP, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.sql.functions import now
from datetime import datetime
from geoalchemy2 import Geometry
from config import settings


class Base(DeclarativeBase):
    pass


class Satellites(Base):
    __tablename__ = "satellites"
    __table_args__ = {"schema": f"{settings.database.schema}"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    norad_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    cospar_id: Mapped[str] = mapped_column(String(length=32), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(length=32), index=True, nullable=False)
    line1: Mapped[str] = mapped_column(String(length=256), nullable=False)
    line2: Mapped[str] = mapped_column(String(length=256), nullable=False)
    epoch: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    mean_motion: Mapped[float] = mapped_column(REAL, nullable=True)
    eccentricity: Mapped[float] = mapped_column(REAL, nullable=True)
    inclination: Mapped[float] = mapped_column(REAL, nullable=True)
    ra_of_asc_node: Mapped[float] = mapped_column(REAL, nullable=True)
    arg_of_pericenter: Mapped[float] = mapped_column(REAL, nullable=True)
    mean_anomaly: Mapped[float] = mapped_column(REAL, nullable=True)
    ephemeris_type: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    classification_type: Mapped[str] = mapped_column(String(length=4), nullable=True)
    element_set_no: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    rev_at_epoch: Mapped[int] = mapped_column(Integer, nullable=True)
    bstar: Mapped[float] = mapped_column(REAL, nullable=True)
    mean_motion_dot: Mapped[float] = mapped_column(REAL, nullable=True)
    mean_motion_ddot: Mapped[float] = mapped_column(REAL, nullable=True)
    last_update: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, server_default=now(), onupdate=now()
    )
    geom: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )

    def __str__(self):
        return f"{self.name}"
