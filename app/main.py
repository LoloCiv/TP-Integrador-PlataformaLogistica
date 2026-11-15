import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from starlette.requests import HTTPConnection

from app.api import auth, clientes, depositos, health, inventario, ordenes, productos, repartidores, rutas, tracking, vehiculos
from app.core.config import settings
from app.core.errores import registrar_manejadores_de_errores
from app.core.logging import configurar_logging
from app.db import crear_tablas
from app.middleware.auth import AuthMiddleware
from app.middleware.log_requests import LogRequestsMiddleware

# Primero el logging, así todo lo que pase después queda registrado
configurar_logging()
logger = logging.getLogger(__name__)


# Lo que corre al arrancar (antes del yield) y al apagar (después) la API
@asynccontextmanager
async def lifespan(app: FastAPI):
    crear_tablas()
    logger.info("API iniciada: tablas verificadas")
    yield
    logger.info("API detenida")


# Solo para que Swagger muestre el botón Authorize; el token lo valida AuthMiddleware
class TokenParaDocs(HTTPBearer):
    async def __call__(self, conexion: HTTPConnection) -> None:
        return None


esquema_token = TokenParaDocs(auto_error=False)

app = FastAPI(title="Plataforma de Logística", lifespan=lifespan, dependencies=[Depends(esquema_token)])

# Traduce las excepciones (NoEncontrado, ValueError...) a respuestas HTTP
registrar_manejadores_de_errores(app)


# Middlewares: el último que se agrega queda más afuera → CORS → Log → Auth → endpoint
app.add_middleware(AuthMiddleware)
app.add_middleware(LogRequestsMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origen.strip() for origen in settings.cors_origins.split(",")], #desde qué páginas web se puede llamar a la API.
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], #qué métodos puede usar un navegador desde esas páginas.
    allow_headers=["Authorization", "Content-Type"], #qué cabeceras puede enviar un navegador desde esas páginas.
)

# Routers: cada uno suma los endpoints de su archivo (lo que se ve en /docs)
app.include_router(health.router)
app.include_router(depositos.router)
app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(productos.router)
app.include_router(inventario.router)
app.include_router(vehiculos.router)
app.include_router(repartidores.router)
app.include_router(ordenes.router)
app.include_router(rutas.router)
app.include_router(tracking.router)
