import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Nombre de la lista de Redis que comparten el backend y el microservicio
NOMBRE_COLA = "cola_rutas"


@dataclass
class Coordenada:
    latitud: float
    longitud: float


@dataclass
# Lo que viaja por Redis: las órdenes y sus paradas (primero el depósito)
class MensajeRuta:
    orden_ids: list[int]
    paradas: list[Coordenada] = field(default_factory=list)

    # Para mandarlo por Redis hay que pasarlo a texto
    def a_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    # El camino inverso: de texto a objeto
    def desde_json(texto: str) -> "MensajeRuta":
        datos = json.loads(texto)
        paradas = [Coordenada(**parada) for parada in datos["paradas"]]
        return MensajeRuta(orden_ids=datos["orden_ids"], paradas=paradas)


# Interfaz: el gestor depende de esto y no de Redis. En los tests se usa una ColaFalsa
class ColaMensajes(ABC):

    @abstractmethod
    def publicar(self, mensaje: MensajeRuta) -> None:
        pass


# Implementación real: hace LPUSH a la lista de Redis
class ColaRedis(ColaMensajes):
    def __init__(self, url: str = settings.redis_url, nombre_cola: str = NOMBRE_COLA):
        self.redis = redis.Redis.from_url(url)
        self.nombre_cola = nombre_cola

    def publicar(self, mensaje: MensajeRuta) -> None:
        self.redis.lpush(self.nombre_cola, mensaje.a_json())
        logger.info("Mensaje de ruta publicado en %s: órdenes %s", self.nombre_cola, mensaje.orden_ids)
