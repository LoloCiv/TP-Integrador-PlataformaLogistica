from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.usuario import Usuario


# Un Usuario con datos de cliente; comparte el id con la tabla usuario
class Cliente(Usuario):
    __tablename__ = "cliente"

    id_cliente: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"), primary_key=True)
    direccion: Mapped[str] = mapped_column(String(200))
    telefono: Mapped[str] = mapped_column(String(30))
    dni: Mapped[str] = mapped_column(String(15), unique=True)

    ordenes: Mapped[list["Orden"]] = relationship("Orden", back_populates="cliente")

    __mapper_args__ = {"polymorphic_identity": "cliente"}

    # Las órdenes que hizo el cliente
    def historial_ordenes(self) -> list["Orden"]:
        return self.ordenes
