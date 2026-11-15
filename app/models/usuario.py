from datetime import datetime

import bcrypt

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


# Base de Cliente y Repartidor (herencia joined-table: la columna tipo dice cuál es)
class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    apellido: Mapped[str] = mapped_column(String(100))
    user_name: Mapped[str] = mapped_column(String(50), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    tipo: Mapped[str] = mapped_column(String(20))

    __mapper_args__ = {
        "polymorphic_on": "tipo",
        "polymorphic_identity": "usuario",
    }

    # Guarda la contraseña hasheada con bcrypt, nunca en texto plano
    def cambiar_password(self, nuevo_password: str) -> None:
        self.password = bcrypt.hashpw(nuevo_password.encode(), bcrypt.gensalt()).decode()

    # Compara la contraseña contra el hash guardado
    def validar_credenciales(self, password: str, user_name: str) -> bool:
        if self.user_name != user_name:
            return False
        return bcrypt.checkpw(password.encode(), self.password.encode())
