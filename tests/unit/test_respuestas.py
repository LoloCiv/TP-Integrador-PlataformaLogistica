import json
from decimal import Decimal

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.respuestas import Paginacion, respuesta_error, respuesta_ok, respuesta_paginada


def body(respuesta) -> dict:
    return json.loads(respuesta.body)


def test_ok():
    respuesta = respuesta_ok({"nombre": "Yerba", "precio": Decimal("10.50")}, status=201)

    assert respuesta.status_code == 201
    assert body(respuesta) == {"status": 201, "data": {"nombre": "Yerba", "precio": 10.5}}


def test_paginada():
    respuesta = respuesta_paginada([{"id": 41}], total=57, limit=20, offset=40)

    assert respuesta.status_code == 200
    assert body(respuesta) == {"status": 200, "data": [{"id": 41}], "paginacion": {"total": 57, "limit": 20, "offset": 40}}


def test_error():
    respuesta = respuesta_error(404, "No existe")

    assert respuesta.status_code == 404
    assert body(respuesta) == {"status": 404, "error": "No existe"}


app_prueba = FastAPI()


@app_prueba.get("/prueba")
def prueba(pag: Paginacion = Depends()):
    return {"limit": pag.limit, "offset": pag.offset}


cliente = TestClient(app_prueba)


def test_paginacion():
    assert cliente.get("/prueba").json() == {"limit": 20, "offset": 0}
    assert cliente.get("/prueba?limit=5&offset=10").json() == {"limit": 5, "offset": 10}


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "limit=hola"])
def test_paginacion_invalida(query):
    assert cliente.get(f"/prueba?{query}").status_code == 422
