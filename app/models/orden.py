from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.db import Base


# Pedido de un cliente. Sus detalles se borran con ella (cascade)
class Orden(Base):
    __tablename__ = "orden"

    id_orden: Mapped[int] = mapped_column(primary_key=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    id_ruta: Mapped[int | None] = mapped_column(ForeignKey("ruta.id_ruta"))
    nro_parada: Mapped[int | None] = mapped_column()
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fecha_entrega: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    direccion_entrega: Mapped[str] = mapped_column(String(255))
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    estado_orden: Mapped[str] = mapped_column(String(20), default="PENDIENTE")

    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="ordenes")
    ruta: Mapped["Ruta | None"] = relationship("Ruta", back_populates="ordenes")
    detalles: Mapped[list["DetalleOrden"]] = relationship(
        "DetalleOrden", back_populates="orden", cascade="all, delete-orphan"
    )

    # Suma los subtotales de los detalles y lo guarda en total
    def calcular_total(self) -> Decimal:
        self.total = sum((detalle.calcular_subtotal() for detalle in self.detalles), Decimal("0"))
        return self.total

    # Agregar o sacar un detalle recalcula el total solo
    def agregar_detalle(self, detalle: "DetalleOrden") -> None:
        self.detalles.append(detalle)
        self.calcular_total()

    def remover_detalle(self, detalle: "DetalleOrden") -> None:
        self.detalles.remove(detalle)
        self.calcular_total()

    # Peso total, para ver si entra en el vehículo
    def calcular_peso(self) -> Decimal:
        return sum((detalle.cantidad * detalle.producto.peso for detalle in self.detalles), Decimal("0"))
