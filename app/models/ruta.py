from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.db import Base


# Agrupa las órdenes de un repartidor + vehículo. Distancia y tiempo los completa el microservicio
class Ruta(Base):
    __tablename__ = "ruta"

    id_ruta: Mapped[int] = mapped_column(primary_key=True)
    id_repartidor: Mapped[int] = mapped_column(ForeignKey("repartidor.id_repartidor"))
    id_vehiculo: Mapped[int] = mapped_column(ForeignKey("vehiculo.id_vehiculo"))
    tiempo_estimado: Mapped[int | None] = mapped_column()
    distancia_km: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))

    repartidor: Mapped["Repartidor"] = relationship("Repartidor", back_populates="rutas")
    vehiculo: Mapped["Vehiculo"] = relationship("Vehiculo", back_populates="rutas")
    ordenes: Mapped[list["Orden"]] = relationship("Orden", back_populates="ruta")
