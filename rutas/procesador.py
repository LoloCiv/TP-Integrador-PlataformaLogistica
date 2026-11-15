import logging

from sqlalchemy import Engine, text

from mensajes import MensajeRuta
from optimizador import RutaOptimizador

logger = logging.getLogger("rutas")


# Guarda los resultados en Postgres con SQL directo
class RepositorioRutas:
    def __init__(self, engine: Engine):
        self.engine = engine

    # Todo en una transacción: nro_parada de cada orden y distancia/tiempo de la ruta
    def guardar(self, paradas: dict[int, int], distancia: float, tiempo: int) -> None:
        with self.engine.begin() as conn:
            for id_orden, nro in paradas.items():
                resultado = conn.execute(
                    text("UPDATE orden SET nro_parada = :nro WHERE id_orden = :id"),
                    {"nro": nro, "id": id_orden},
                )
                if resultado.rowcount == 0:
                    logger.warning("No se encontró la orden %s al guardar su número de parada", id_orden)
            # Busca la ruta a partir de alguna de las órdenes
            id_ruta = None
            for id_orden in paradas:
                id_ruta = conn.scalar(
                    text("SELECT id_ruta FROM orden WHERE id_orden = :id"), {"id": id_orden}
                )
                if id_ruta is not None:
                    break
            if id_ruta is not None:
                logger.info("Guardando distancia %s km y tiempo %s min para la ruta %s", distancia, tiempo, id_ruta)
            else:
                logger.warning("No se pudo determinar la ruta para guardar la distancia y tiempo")
                return
            conn.execute(
                text("UPDATE ruta SET distancia_km = :d, tiempo_estimado = :t WHERE id_ruta = :r"),
                {"d": distancia, "t": tiempo, "r": id_ruta},
            )


# Optimiza el recorrido y lo guarda. Recibe optimizador y repositorio por constructor
class ProcesadorRutas:

    def __init__(self, optimizador: RutaOptimizador, repositorio: RepositorioRutas):
        self.optimizador = optimizador
        self.repositorio = repositorio

    def procesar(self, mensaje: MensajeRuta) -> dict[int, int]:
        recorrido = self.optimizador.optimizar(mensaje.paradas)

        # Empareja cada coordenada con su orden (salteando el depósito) y le asigna su número de parada
        pendientes = list(zip(mensaje.paradas[1:], mensaje.orden_ids))
        paradas: dict[int, int] = {}
        for nro, coordenada in enumerate(recorrido[1:], start=1):
            par = next(pendiente for pendiente in pendientes if pendiente[0] == coordenada)
            pendientes.remove(par)
            paradas[par[1]] = nro

        tiempo = self.optimizador.estimar_tiempo()
        self.repositorio.guardar(paradas, self.optimizador.distancia_total, tiempo)
        logger.info("Ruta calculada: paradas %s, %s km, %s min", paradas, self.optimizador.distancia_total, tiempo)
        return paradas
