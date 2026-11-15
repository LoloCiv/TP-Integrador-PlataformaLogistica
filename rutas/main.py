import logging
import os
import time

import redis
from sqlalchemy import create_engine

from mensajes import MensajeRuta
from optimizador import OptimizadorRutas
from procesador import ProcesadorRutas, RepositorioRutas

# La misma lista de Redis que usa el backend
NOMBRE_COLA = "cola_rutas"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
logger = logging.getLogger("rutas")


# Datos de Postgres desde las variables de entorno (no comparte código con el backend)
def url_base() -> str:
    entorno = os.environ
    return (
        f"postgresql+psycopg://{entorno['POSTGRES_USER']}:{entorno['POSTGRES_PASSWORD']}"
        f"@{entorno.get('POSTGRES_HOST', 'db')}:{entorno.get('POSTGRES_PORT', '5432')}/{entorno['POSTGRES_DB']}"
    )


# Bucle infinito: espera mensajes en Redis y los procesa
def main() -> None:
    cola = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://redis:6379/0"))
    procesador = ProcesadorRutas(OptimizadorRutas(), RepositorioRutas(create_engine(url_base())))
    logger.info("Escuchando la cola %s...", NOMBRE_COLA)

    while True:
        # Espera hasta 2 segundos un mensaje; si no llega, vuelve a intentar
        try:
            resultado = cola.brpop(NOMBRE_COLA, timeout=2)
        except (redis.ConnectionError, redis.TimeoutError):
            logger.warning("Redis no responde, reintento en 3 segundos")
            time.sleep(3)
            continue

        if resultado is None:
            continue
        _, dato = resultado

        # Si un mensaje falla se loguea y se sigue con el próximo
        try:
            procesador.procesar(MensajeRuta.desde_json(dato))
        except Exception:
            logger.exception("No se pudo procesar el mensaje %s", dato)


if __name__ == "__main__":
    main()
