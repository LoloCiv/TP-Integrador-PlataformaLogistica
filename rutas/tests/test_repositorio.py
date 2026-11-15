import logging

import pytest
from sqlalchemy import create_engine, text

from procesador import RepositorioRutas


# SQLite en memoria con solo las columnas de orden y ruta que usa el microservicio
@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE orden (
                id_orden INTEGER PRIMARY KEY,
                nro_parada INTEGER,
                id_ruta INTEGER
            )
        """))
        conn.execute(text("""
            CREATE TABLE ruta (
                id_ruta INTEGER PRIMARY KEY,
                distancia_km FLOAT,
                tiempo_estimado INTEGER
            )
        """))
        conn.execute(text("""
            INSERT INTO ruta (id_ruta, distancia_km, tiempo_estimado)
            VALUES (1, 0, 0)
        """))
        conn.execute(text("""
            INSERT INTO orden (id_orden, nro_parada, id_ruta)
            VALUES (10, NULL, 1)
        """))
    yield engine
    engine.dispose()


# Si una orden del mensaje no existe en la base, se loguea un aviso y no falla
def test_orden_fantasma(engine, caplog):
    with caplog.at_level(logging.WARNING, logger="rutas"):
        RepositorioRutas(engine).guardar({999: 1}, 3.5, 7)

    assert "No se encontró la orden 999" in caplog.text


# Aunque la primera orden no exista, la ruta se encuentra con la siguiente y se guardan distancia y tiempo
def test_primera_fantasma(engine, caplog):
    with caplog.at_level(logging.WARNING, logger="rutas"):
        RepositorioRutas(engine).guardar({999: 1, 10: 2}, 3.5, 7)

    with engine.begin() as conn:
        ruta = conn.execute(
            text("SELECT distancia_km, tiempo_estimado FROM ruta WHERE id_ruta = 1")
        ).one()

    assert ruta == (3.5, 7)
    assert "No se encontró la orden 999" in caplog.text
