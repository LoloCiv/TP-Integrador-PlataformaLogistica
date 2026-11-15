from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# Lo que entra al registrarse (todo obligatorio)
class ClienteCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    user_name: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    direccion: str = Field(min_length=1, max_length=200)
    telefono: str = Field(min_length=6, max_length=30)
    dni: str = Field(pattern=r"^\d{7,8}$")


# Para PATCH: todo opcional
class ClienteActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    apellido: str | None = Field(default=None, min_length=1, max_length=100)
    direccion: str | None = Field(default=None, min_length=1, max_length=200)
    telefono: str | None = Field(default=None, min_length=6, max_length=30)


# Lo que se devuelve: sin la contraseña
class ClienteSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    nombre: str
    apellido: str
    user_name: str
    direccion: str
    telefono: str
    dni: str
    fecha_registro: datetime
