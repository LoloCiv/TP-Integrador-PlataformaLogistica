from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.db import Base


# Stock de un producto (uno a uno)
class Inventario(Base):
    __tablename__ = "inventario"

    id_inventario: Mapped[int] = mapped_column(primary_key=True)
    id_producto: Mapped[int] = mapped_column(ForeignKey("producto.id_producto"), unique=True)
    stock_actual: Mapped[int] = mapped_column()
    ultima_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    producto: Mapped["Producto"] = relationship("Producto", back_populates="inventario")


    def consultar_stock(self) -> int:
        return self.stock_actual

    def hay_stock_suficiente(self, cantidad: int) -> bool:
        return self.stock_actual >= cantidad

    # Resta stock validando la cantidad y que alcance
    def descontar_stock(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad a descontar debe ser mayor a 0")
        if not self.hay_stock_suficiente(cantidad):
            raise ValueError(f"Stock insuficiente: hay {self.stock_actual}, se pidieron {cantidad}")
        self.stock_actual -= cantidad
