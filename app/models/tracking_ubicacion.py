from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.db import Base


# Última posición conocida de cada repartidor (una fila por repartidor)
class TrackingUbicacion(Base):
    __tablename__ = "tracking_ubicacion"

    id_tracking_ubicacion: Mapped[int] = mapped_column(primary_key=True)
    latitud: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    longitud: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    ultima_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    id_repartidor: Mapped[int] = mapped_column(ForeignKey("repartidor.id_repartidor"), unique=True)

    repartidor: Mapped["Repartidor"] = relationship("Repartidor", back_populates="tracking_ubicacion")


    # Valida los rangos de latitud y longitud antes de guardar
    def actualizar_posicion(self, nueva_latitud: Decimal, nueva_longitud: Decimal) -> None:
        if not (-90 <= nueva_latitud <= 90):
            raise ValueError("Latitud inválida: debe estar entre -90 y 90")
        if not (-180 <= nueva_longitud <= 180):
            raise ValueError("Longitud inválida: debe estar entre -180 y 180")
        self.latitud = nueva_latitud
        self.longitud = nueva_longitud
