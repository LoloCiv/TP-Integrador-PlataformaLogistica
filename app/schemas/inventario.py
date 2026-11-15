from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# Stock inicial de un producto
class InventarioCrear(BaseModel):
    id_producto: int
    stock_actual: int = Field(ge=0)


# Para ajustar el stock a mano
class InventarioActualizar(BaseModel):
    stock_actual: int = Field(ge=0)


# Lo que se devuelve
class InventarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_inventario: int
    id_producto: int
    stock_actual: int
    ultima_actualizacion: datetime
