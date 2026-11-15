from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.db import Base


# Cada producto pertenece a un depósito y tiene su inventario
class Producto(Base):
    __tablename__ = "producto"

    id_producto: Mapped[int] = mapped_column(primary_key=True)
    id_deposito: Mapped[int] = mapped_column(ForeignKey("deposito.id_deposito"))
    nombre: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str | None] = mapped_column(Text)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    peso: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    categoria: Mapped[str] = mapped_column(String(50))
    deposito: Mapped["Deposito"] = relationship("Deposito", back_populates="productos")
    inventario: Mapped["Inventario | None"] = relationship("Inventario", back_populates="producto")


    # La forma de cambiar el precio: valida que sea mayor a 0
    def actualizar_precio(self,nuevo_precio) -> None:
        if nuevo_precio<=0:
            raise ValueError("El precio debe ser mayor a 0")
        self.precio=nuevo_precio
