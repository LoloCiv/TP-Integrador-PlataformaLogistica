import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.security import crear_token
from app.middleware.auth import AuthMiddleware, es_publica

app_prueba = FastAPI()
app_prueba.add_middleware(AuthMiddleware)


@app_prueba.get("/productos/{id}")
def ver_producto(id: int):
    return {"id": id}


@app_prueba.get("/ordenes")
def listar_ordenes(request: Request):
    return {"usuario": request.state.usuario}


cliente = TestClient(app_prueba)


def test_publica():
    assert cliente.get("/productos/5").status_code == 200


@pytest.mark.parametrize("header", [
    None,
    crear_token(7, "cliente"),
    "Bearer cualquiera",
    f"Bearer {crear_token(7, 'cliente', expira_minutos=-1)}",
])
def test_privada_sin_token_valido(header):
    headers = {"Authorization": header} if header else {}

    assert cliente.get("/ordenes", headers=headers).status_code == 401


def test_token_valido():
    respuesta = cliente.get("/ordenes", headers={"Authorization": f"Bearer {crear_token(7, 'cliente')}"})

    assert respuesta.status_code == 200
    assert respuesta.json()["usuario"]["sub"] == "7"
    assert respuesta.json()["usuario"]["rol"] == "cliente"


def test_es_publica():
    assert es_publica("GET", "/productos") is True
    assert es_publica("GET", "/productos/5") is True
    assert es_publica("POST", "/clientes") is True
    assert es_publica("GET", "/productos-eliminados") is False
    assert es_publica("PUT", "/productos/5") is False
    assert es_publica("POST", "/clientes/3/ordenes") is False
