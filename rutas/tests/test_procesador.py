from unittest.mock import Mock

from mensajes import Coordenada, MensajeRuta
from optimizador import OptimizadorRutas, RutaOptimizador
from procesador import ProcesadorRutas

# El depósito siempre es la primera parada del mensaje
DEPOSITO = Coordenada(0, 0)


# Numera cada orden según el recorrido optimizado y guarda distancia y tiempo.
# El repositorio es un Mock, así que no hace falta base
def test_numera_paradas():
    mensaje = MensajeRuta(orden_ids=[10, 20, 30],
                          paradas=[DEPOSITO, Coordenada(3, 3), Coordenada(2, 2), Coordenada(1, 1)])
    optimizador, repositorio = OptimizadorRutas(), Mock()

    ProcesadorRutas(optimizador, repositorio).procesar(mensaje)

    repositorio.guardar.assert_called_once_with(
        {30: 1, 20: 2, 10: 3}, optimizador.distancia_total, optimizador.estimar_tiempo()
    )


# Con un optimizador falso que invierte las entregas, el procesador numera según lo que devuelve:
# depende de la interfaz RutaOptimizador y no de la implementación
def test_optimizador_mock():
    optimizador = Mock(spec=RutaOptimizador)
    optimizador.optimizar.side_effect = lambda puntos: [puntos[0]] + puntos[1:][::-1]
    optimizador.distancia_total = 12.5
    optimizador.estimar_tiempo.return_value = 25
    repositorio = Mock()
    mensaje = MensajeRuta(orden_ids=[1, 2], paradas=[DEPOSITO, Coordenada(1, 1), Coordenada(2, 2)])

    ProcesadorRutas(optimizador, repositorio).procesar(mensaje)

    repositorio.guardar.assert_called_once_with({2: 1, 1: 2}, 12.5, 25)
