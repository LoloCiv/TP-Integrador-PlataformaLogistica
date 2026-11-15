import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api.request")


# Escribe una línea de log por pedido: método, ruta, status, tiempo y usuario
class LogRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        inicio = time.perf_counter()
        ruta = request.url.path
        if request.url.query:
            ruta += f"?{request.url.query}"

        # Deja pasar el pedido y espera la respuesta
        try:
            respuesta = await call_next(request)
        except Exception:
            logger.exception("%s %s → error no manejado", request.method, ruta)
            raise

        milisegundos = (time.perf_counter() - inicio) * 1000

        # Quién fue (lo dejó AuthMiddleware); '-' si no había token
        usuario = getattr(request.state, "usuario", None)
        id_usuario = usuario["sub"] if usuario else "-"

        # Nivel según cómo terminó: 5xx error, 4xx warning, el resto info
        status = respuesta.status_code
        if status >= 500:
            nivel = logging.ERROR
        elif status >= 400:
            nivel = logging.WARNING
        else:
            nivel = logging.INFO

        logger.log(nivel, "%s %s → %s (%.0f ms) user=%s", request.method, ruta, status, milisegundos, id_usuario)
        return respuesta
