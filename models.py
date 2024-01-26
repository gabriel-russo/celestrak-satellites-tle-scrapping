from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from config import settings


class Base(DeclarativeBase):
    pass


class Satellites(Base):
    __tablename__ = "satellites"
    __table_args__ = {"schema": f"{settings.database.schema}"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    norad_id: Mapped[int] = mapped_column(Integer, nullable=True)
    cospar_id: Mapped[str] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String)
    line1: Mapped[str] = mapped_column(String)
    line2: Mapped[str] = mapped_column(String)

    def __str__(self):
        return f"{self.name}"
