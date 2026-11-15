import json
from dataclasses import dataclass, field


@dataclass
class Coordenada:
    latitud: float
    longitud: float


# El mismo formato que manda el backend, definido de nuevo acá (no comparten código)
@dataclass
class MensajeRuta:
    orden_ids: list[int]
    paradas: list[Coordenada] = field(default_factory=list)

    @staticmethod
    def desde_json(texto: str | bytes) -> "MensajeRuta":
        datos = json.loads(texto)
        paradas = [Coordenada(**parada) for parada in datos["paradas"]]
        return MensajeRuta(orden_ids=datos["orden_ids"], paradas=paradas)
