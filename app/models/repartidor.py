from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import EstadoRepartidor
from app.models.usuario import Usuario


# Un Usuario con datos de repartidor
class Repartidor(Usuario):
    __tablename__ = "repartidor"

    id_repartidor: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"), primary_key=True)
    legajo: Mapped[str] = mapped_column(String(20), unique=True)
    sueldo: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    licencia: Mapped[str] = mapped_column(String(20), unique=True)
    estado_repartidor: Mapped[str] = mapped_column(String(20))

    vehiculos: Mapped[list["Vehiculo"]] = relationship("Vehiculo", back_populates="repartidor")
    rutas: Mapped[list["Ruta"]] = relationship("Ruta", back_populates="repartidor")
    tracking_ubicacion: Mapped["TrackingUbicacion | None"] = relationship(
        "TrackingUbicacion", back_populates="repartidor"
    )


    __mapper_args__ = {"polymorphic_identity": "repartidor"}

    # Solo se le pueden asignar órdenes si está DISPONIBLE
    def esta_disponible(self) -> bool:
        return self.estado_repartidor == EstadoRepartidor.DISPONIBLE

    # Valida que el estado sea uno del enum
    def cambiar_estado(self, nuevo_estado: EstadoRepartidor) -> None:
        if nuevo_estado not in EstadoRepartidor:
            raise ValueError(f"Estado de repartidor inválido: {nuevo_estado}")
        self.estado_repartidor = nuevo_estado
