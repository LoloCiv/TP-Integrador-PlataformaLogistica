from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EstadoOrden


# Un renglón del pedido: qué producto y cuántos
class DetalleOrdenCrear(BaseModel):
    id_producto: int
    cantidad: int = Field(gt=0)


# Body para crear una orden. El cliente sale del token, no de acá
class OrdenCrear(BaseModel):
    direccion_entrega: str = Field(min_length=1, max_length=255)
    latitud: Decimal = Field(ge=-90, le=90)
    longitud: Decimal = Field(ge=-180, le=180)
    detalles: list[DetalleOrdenCrear] = Field(min_length=1)


# Body de /asignar
class AsignarRepartidorEntrada(BaseModel):
    id_repartidor: int
    id_vehiculo: int


# Body de /estado; solo acepta valores del enum
class CambiarEstadoEntrada(BaseModel):
    estado_orden: EstadoOrden


class DetalleOrdenSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_detalle_orden: int
    id_producto: int
    cantidad: int
    precio_unitario: Decimal


# Lo que se devuelve de una orden, con sus detalles
class OrdenSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_orden: int
    id_cliente: int
    id_ruta: int | None
    nro_parada: int | None
    fecha_creacion: datetime
    fecha_entrega: datetime | None
    total: Decimal
    direccion_entrega: str
    latitud: Decimal | None
    longitud: Decimal | None
    estado_orden: EstadoOrden
    detalles: list[DetalleOrdenSalida]
