from enum import StrEnum

# Estados posibles de cada entidad. Al ser StrEnum se guardan como texto
class EstadoRepartidor(StrEnum):
    DISPONIBLE = "DISPONIBLE"
    EN_RUTA = "EN_RUTA"
    INACTIVO = "INACTIVO"

# PENDIENTE → CONFIRMADA → EN_CAMINO → ENTREGADA (o CANCELADA antes de salir)
class EstadoOrden(StrEnum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    EN_CAMINO = "EN_CAMINO"
    ENTREGADA = "ENTREGADA"
    CANCELADA = "CANCELADA"

class EstadoVehiculo(StrEnum):
    DISPONIBLE = "DISPONIBLE"
    EN_USO = "EN_USO"
    MANTENIMIENTO = "MANTENIMIENTO"
    INACTIVO = "INACTIVO"

class TipoVehiculo(StrEnum):
    MOTO = "MOTO"
    AUTO = "AUTO"
    CAMIONETA = "CAMIONETA"
    BICICLETA = "BICICLETA"
