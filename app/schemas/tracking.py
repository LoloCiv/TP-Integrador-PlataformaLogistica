from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# Lo que manda el repartidor con su posición
class PosicionEntrada(BaseModel):
    latitud: Decimal = Field(ge=-90, le=90)
    longitud: Decimal = Field(ge=-180, le=180)


# Lo que se devuelve y se reenvía por WebSocket
class TrackingSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_repartidor: int
    latitud: Decimal
    longitud: Decimal
    ultima_actualizacion: datetime
