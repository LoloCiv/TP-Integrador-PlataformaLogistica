from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import EstadoVehiculo


# Vehículo de un repartidor, con su capacidad en kg
class Vehiculo(Base):
    __tablename__ = "vehiculo"

    id_vehiculo: Mapped[int] = mapped_column(primary_key=True)
    id_repartidor: Mapped[int | None] = mapped_column(ForeignKey("repartidor.id_repartidor"))
    patente: Mapped[str] = mapped_column(String(10), unique=True)
    marca: Mapped[str] = mapped_column(String(50))
    tipo_vehiculo: Mapped[str] = mapped_column(String(20))
    modelo: Mapped[str] = mapped_column(String(50))
    capacidad_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    estado_vehiculo: Mapped[str] = mapped_column(String(20))

    repartidor: Mapped["Repartidor | None"] = relationship("Repartidor", back_populates="vehiculos")
    rutas: Mapped[list["Ruta"]] = relationship("Ruta", back_populates="vehiculo")

    # Para asignarle órdenes tiene que estar DISPONIBLE
    def esta_disponible(self) -> bool:
        return self.estado_vehiculo == EstadoVehiculo.DISPONIBLE

    def cambiar_estado(self, nuevo_estado: EstadoVehiculo) -> None:
        if nuevo_estado not in EstadoVehiculo:
            raise ValueError(f"Estado de vehículo inválido: {nuevo_estado}")
        self.estado_vehiculo = nuevo_estado
