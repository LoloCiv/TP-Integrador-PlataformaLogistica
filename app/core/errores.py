import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.respuestas import respuesta_error

logger = logging.getLogger(__name__)


# Error propio para cuando algo no existe → 404
class NoEncontrado(Exception):
    pass

# Cada handler convierte un tipo de excepción en una respuesta {status, error}
def registrar_manejadores_de_errores(app: FastAPI) -> None:

    @app.exception_handler(NoEncontrado)
    async def error_no_encontrado(request, error):
        return respuesta_error(404, str(error))

    @app.exception_handler(StarletteHTTPException)
    async def error_http(request, error):
        return respuesta_error(error.status_code, str(error.detail))

    @app.exception_handler(RequestValidationError)
    async def error_validacion(request, error):
        problemas = [f"{'.'.join(str(parte) for parte in problema['loc'][1:])}: {problema['msg']}" for problema in error.errors()]
        return respuesta_error(422, "; ".join(problemas))

    @app.exception_handler(IntegrityError)
    async def error_integridad(request, error):
        return respuesta_error(409, "Conflicto con datos existentes: valor duplicado o en uso")

    # Las reglas de negocio rotas (stock, estados...) se lanzan como ValueError → 400
    @app.exception_handler(ValueError)
    async def error_regla_de_negocio(request, error):
        return respuesta_error(400, str(error))

    # Cualquier otra cosa: 500 sin mostrar detalles internos
    @app.exception_handler(Exception)
    async def error_inesperado(request, error):
        return respuesta_error(500, "Error interno del servidor")
