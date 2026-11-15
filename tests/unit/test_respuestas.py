import json
from decimal import Decimal

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.respuestas import Paginacion, respuesta_error, respuesta_ok, respuesta_paginada


# Lee el JSON de una respuesta armada a mano
def body(respuesta) -> dict:
    return json.loads(respuesta.body)


# Formato de éxito {status, data}; los Decimal salen como número
def test_ok():
    respuesta = respuesta_ok({"nombre": "Yerba", "precio": Decimal("10.50")}, status=201)

    assert respuesta.status_code == 201
    assert body(respuesta) == {"status": 201, "data": {"nombre": "Yerba", "precio": 10.5}}


# Formato paginado: agrega total, limit y offset
def test_paginada():
    respuesta = respuesta_paginada([{"id": 41}], total=57, limit=20, offset=40)

    assert respuesta.status_code == 200
    assert body(respuesta) == {"status": 200, "data": [{"id": 41}], "paginacion": {"total": 57, "limit": 20, "offset": 40}}


# Formato de error {status, error}
def test_error():
    respuesta = respuesta_error(404, "No existe")

    assert respuesta.status_code == 404
    assert body(respuesta) == {"status": 404, "error": "No existe"}


# App mínima para probar la dependencia Paginacion
app_prueba = FastAPI()


@app_prueba.get("/prueba")
def prueba(pag: Paginacion = Depends()):
    return {"limit": pag.limit, "offset": pag.offset}


cliente = TestClient(app_prueba)


# Sin parámetros usa los valores por defecto (limit 20, offset 0)
def test_paginacion():
    assert cliente.get("/prueba").json() == {"limit": 20, "offset": 0}
    assert cliente.get("/prueba?limit=5&offset=10").json() == {"limit": 5, "offset": 10}


# limit fuera de 1-100, offset negativo o texto: 422 de Pydantic
@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "limit=hola"])
def test_paginacion_invalida(query):
    assert cliente.get(f"/prueba?{query}").status_code == 422
