from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# Solo salida: las rutas no se crean a mano, las arma el sistema
class RutaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_ruta: int
    id_repartidor: int
    id_vehiculo: int
    tiempo_estimado: int | None
    distancia_km: Decimal | None
