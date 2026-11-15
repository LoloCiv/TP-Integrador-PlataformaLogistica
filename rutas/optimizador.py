import math
from abc import ABC, abstractmethod

from mensajes import Coordenada

# Velocidad promedio supuesta para estimar el tiempo
VELOCIDAD_KMH = 30


# Distancia en km entre dos puntos de la Tierra (fórmula de Haversine)
def distancia_km(a: Coordenada, b: Coordenada) -> float:
    radio_tierra = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [a.latitud, a.longitud, b.latitud, b.longitud])
    valor_haversine = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * radio_tierra * math.asin(math.sqrt(valor_haversine))


# Interfaz del optimizador: se puede cambiar el algoritmo sin tocar el procesador
class RutaOptimizador(ABC):
    distancia_total: float = 0.0

    @abstractmethod
    def optimizar(self, puntos: list[Coordenada]) -> list[Coordenada]:
        ...

    @abstractmethod
    def estimar_tiempo(self) -> int:
        ...


# Vecino más cercano: desde el depósito, siempre al punto pendiente más cerca
class OptimizadorRutas(RutaOptimizador):
    def optimizar(self, puntos: list[Coordenada]) -> list[Coordenada]:
        actual = puntos[0]
        pendientes = puntos[1:]
        ordenados = [actual]
        distancia_total = 0.0
        while pendientes:
            siguiente = min(pendientes, key=lambda punto: distancia_km(actual, punto))
            distancia_total += distancia_km(actual, siguiente)
            pendientes.remove(siguiente)
            ordenados.append(siguiente)
            actual = siguiente
        self.distancia_total = round(distancia_total, 2)
        return ordenados

    # Minutos a partir de la distancia, como mínimo 1
    def estimar_tiempo(self) -> int:
        minutos = math.ceil(self.distancia_total / VELOCIDAD_KMH * 60)
        return max(1, minutos)
