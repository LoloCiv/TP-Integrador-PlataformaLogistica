from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.db import Base


# Lugar donde están los productos y desde donde salen las rutas
class Deposito(Base):
    __tablename__ = "deposito"

    id_deposito: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    direccion: Mapped[str] = mapped_column(String(255))
    latitud: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    longitud: Mapped[Decimal] = mapped_column(Numeric(9, 6))

    productos:Mapped[list["Producto"]] = relationship("Producto", back_populates="deposito")

    def listar_productos(self) -> list["Producto"]:
        return self.productos
