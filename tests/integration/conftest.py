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

BASE_TEST = f"{settings.postgres_db}_test"
SERVIDOR = settings.database_url.rsplit("/", 1)[0]


class ColaFalsa(ColaMensajes):
    def __init__(self):
        self.mensajes = []

    def publicar(self, mensaje):
        self.mensajes.append(mensaje)


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


@pytest.fixture
def anyio_backend():
    return "asyncio"


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


@pytest.fixture
def db(engine):
    sesion = sessionmaker(bind=engine)()
    yield sesion
    sesion.close()
