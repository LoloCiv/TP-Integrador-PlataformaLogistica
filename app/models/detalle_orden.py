from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.db import Base


# Un renglón de la orden: producto, cantidad y precio
class DetalleOrden(Base):
    __tablename__ = "detalle_orden"

    id_detalle_orden: Mapped[int] = mapped_column(primary_key=True)
    id_orden: Mapped[int] = mapped_column(ForeignKey("orden.id_orden"))
    id_producto: Mapped[int] = mapped_column(ForeignKey("producto.id_producto"))
    cantidad: Mapped[int] = mapped_column()
    # Foto del precio al comprar: si después cambia el producto, esto queda igual
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    orden: Mapped["Orden"] = relationship("Orden", back_populates="detalles")
    producto: Mapped["Producto"] = relationship("Producto")

    def calcular_subtotal(self) -> Decimal:
        return self.cantidad * self.precio_unitario
