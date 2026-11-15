from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# Lo que entra al crear (y en el PUT)
class ProductoCrear(BaseModel):
    id_deposito: int
    nombre: str = Field(min_length=1, max_length=150)
    descripcion: str | None = None
    precio: Decimal = Field(gt=0)
    peso: Decimal = Field(gt=0)
    categoria: str = Field(min_length=1, max_length=50)


# Para PATCH: todo opcional
class ProductoActualizar(BaseModel):
    id_deposito: int | None = None
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = None
    precio: Decimal | None = Field(default=None, gt=0)
    peso: Decimal | None = Field(default=None, gt=0)
    categoria: str | None = Field(default=None, min_length=1, max_length=50)


# Lo que se devuelve
class ProductoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_producto: int
    id_deposito: int
    nombre: str
    descripcion: str | None
    precio: Decimal
    peso: Decimal
    categoria: str
    fecha_creacion: datetime
