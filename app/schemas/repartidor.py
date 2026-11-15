from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EstadoRepartidor


# Lo que entra al crear un repartidor
class RepartidorCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    user_name: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    legajo: str = Field(min_length=1, max_length=20)
    sueldo: Decimal = Field(gt=0)
    licencia: str = Field(min_length=1, max_length=20)
    estado_repartidor: EstadoRepartidor = EstadoRepartidor.DISPONIBLE


# Para PATCH: todo opcional
class RepartidorActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    apellido: str | None = Field(default=None, min_length=1, max_length=100)
    sueldo: Decimal | None = Field(default=None, gt=0)
    licencia: str | None = Field(default=None, min_length=1, max_length=20)
    estado_repartidor: EstadoRepartidor | None = None


# Lo que se devuelve: sin la contraseña
class RepartidorSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    nombre: str
    apellido: str
    user_name: str
    legajo: str
    sueldo: Decimal
    licencia: str
    estado_repartidor: EstadoRepartidor
    fecha_registro: datetime
