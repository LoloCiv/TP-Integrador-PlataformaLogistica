from starlette.middleware.base import BaseHTTPMiddleware

from app.core.respuestas import respuesta_error
from app.core.security import decodificar_token

# Rutas que se pueden usar sin token
RUTAS_PUBLICAS = [
    ("POST", "/auth/login"),
    ("POST", "/clientes"),
    ("GET", "/productos"),
    ("GET", "/depositos"),
    ("GET", "/health"),
    ("GET", "/docs"),
    ("GET", "/openapi.json"),
]


# Se fija si el pedido es a una ruta pública (en los GET también cubre /productos/3, etc.)
def es_publica(metodo: str, ruta: str) -> bool:
    for metodo_publico, ruta_publica in RUTAS_PUBLICAS:
        if metodo != metodo_publico:
            continue
        if ruta == ruta_publica:
            return True
        if metodo == "GET" and ruta.startswith(ruta_publica + "/"):
            return True
    return False


# Corre en cada pedido: si la ruta no es pública, exige un token válido
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if es_publica(request.method, request.url.path):
            return await call_next(request)


        autorizacion = request.headers.get("Authorization")
        if not autorizacion or not autorizacion.startswith("Bearer "):
            return respuesta_error(401, "Falta el token de autenticación")

        token = autorizacion.removeprefix("Bearer ")

        try:
            payload = decodificar_token(token)
        except ValueError as error:
            return respuesta_error(401, str(error))

        # Deja los datos del token para los que vienen después (endpoints, log)
        request.state.usuario = payload

        return await call_next(request)
