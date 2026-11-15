# Tests de integración: usan un Postgres real (una base aparte, <nombre>_test),
# así que necesitan el contenedor db levantado
import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.api.ordenes import obtener_gestor
from app.core.config import settings
from app.db import Base, get_db
from app.main import app
from app.services.cola_mensajes import ColaMensajes
from app.services.gestor_pedidos import GestorPedidos

# Base de los tests, en el mismo servidor que la base real
BASE_TEST = f"{settings.postgres_db}_test"
SERVIDOR = settings.database_url.rsplit("/", 1)[0]


# Cola de prueba: guarda los mensajes en vez de mandarlos a Redis
class ColaFalsa(ColaMensajes):
    def __init__(self):
        self.mensajes = []

    def publicar(self, mensaje):
        self.mensajes.append(mensaje)


# Una vez por corrida: crea la base de test si no existe y arma las tablas de cero
@pytest.fixture(scope="session")
def engine():
    admin = create_engine(f"{SERVIDOR}/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        if not conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :nombre"), {"nombre": BASE_TEST}):
            conn.execute(text(f'CREATE DATABASE "{BASE_TEST}"'))
    admin.dispose()

    engine = create_engine(f"{SERVIDOR}/{BASE_TEST}")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


# Los tests son async y corren con asyncio
@pytest.fixture
def anyio_backend():
    return "asyncio"


# Cliente HTTP contra la app real, con la base de test y la cola falsa.
# Al terminar cada test vacía todas las tablas
@pytest.fixture
async def cliente(engine):
    Sesion = sessionmaker(bind=engine)

    def db_test():
        db = Sesion()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = db_test
    app.dependency_overrides[obtener_gestor] = lambda db=Depends(get_db): GestorPedidos(db, ColaFalsa())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente_http:
        yield cliente_http

    app.dependency_overrides.clear()
    tablas = ", ".join(tabla.name for tabla in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))


# Sesión para revisar directamente en la base lo que hizo la API
@pytest.fixture
def db(engine):
    sesion = sessionmaker(bind=engine)()
    yield sesion
    sesion.close()
