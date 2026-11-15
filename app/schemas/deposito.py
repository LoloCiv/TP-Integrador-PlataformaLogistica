from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# Lo que entra al crear (todo obligatorio)
class DepositoCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    direccion: str = Field(min_length=1, max_length=255)
    latitud: Decimal = Field(ge=-90, le=90)
    longitud: Decimal = Field(ge=-180, le=180)


# Para PATCH: todo opcional
class DepositoActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    direccion: str | None = Field(default=None, min_length=1, max_length=255)
    latitud: Decimal | None = Field(default=None, ge=-90, le=90)
    longitud: Decimal | None = Field(default=None, ge=-180, le=180)


# Lo que se devuelve. from_attributes permite armarlo desde el objeto del ORM
class DepositoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_deposito: int
    nombre: str
    direccion: str
    latitud: Decimal
    longitud: Decimal
