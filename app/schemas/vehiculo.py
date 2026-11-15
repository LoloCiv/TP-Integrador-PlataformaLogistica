from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EstadoVehiculo, TipoVehiculo


# Lo que entra al crear (y en el PUT)
class VehiculoCrear(BaseModel):
    patente: str = Field(min_length=6, max_length=10)
    marca: str = Field(min_length=1, max_length=50)
    modelo: str = Field(min_length=1, max_length=50)
    tipo_vehiculo: TipoVehiculo
    capacidad_kg: Decimal = Field(gt=0)
    id_repartidor: int | None = None
    estado_vehiculo: EstadoVehiculo = EstadoVehiculo.DISPONIBLE


# Para PATCH: todo opcional
class VehiculoActualizar(BaseModel):
    marca: str | None = Field(default=None, min_length=1, max_length=50)
    modelo: str | None = Field(default=None, min_length=1, max_length=50)
    tipo_vehiculo: TipoVehiculo | None = None
    capacidad_kg: Decimal | None = Field(default=None, gt=0)
    id_repartidor: int | None = None
    estado_vehiculo: EstadoVehiculo | None = None


# Lo que se devuelve
class VehiculoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_vehiculo: int
    patente: str
    marca: str
    modelo: str
    tipo_vehiculo: TipoVehiculo
    capacidad_kg: Decimal
    id_repartidor: int | None
    estado_vehiculo: EstadoVehiculo
