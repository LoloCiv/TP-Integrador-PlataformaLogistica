from mensajes import Coordenada
from optimizador import OptimizadorRutas, distancia_km


def test_vecino_cercano():
    optimizador = OptimizadorRutas()
    puntos = [Coordenada(0, 0), Coordenada(3, 3), Coordenada(1, 1), Coordenada(2, 2)]

    recorrido = optimizador.optimizar(puntos)

    assert [(punto.latitud, punto.longitud) for punto in recorrido] == [(0, 0), (1, 1), (2, 2), (3, 3)]
    assert [(punto.latitud, punto.longitud) for punto in puntos] == [(0, 0), (3, 3), (1, 1), (2, 2)]


def test_distancia_tiempo():
    optimizador = OptimizadorRutas()
    origen, destino = Coordenada(0, 0), Coordenada(1, 1)

    optimizador.optimizar([origen, destino])

    assert optimizador.distancia_total == round(distancia_km(origen, destino), 2)
    optimizador.distancia_total = 15
    assert optimizador.estimar_tiempo() == 30


def test_tiempo_minimo():
    optimizador = OptimizadorRutas()

    optimizador.optimizar([Coordenada(0, 0), Coordenada(0, 0)])

    assert optimizador.estimar_tiempo() == 1
