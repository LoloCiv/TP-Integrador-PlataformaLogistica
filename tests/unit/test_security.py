import jwt
import pytest

from app.core.config import settings
from app.core.security import crear_token, decodificar_token


def test_token():
    payload = decodificar_token(crear_token(id_usuario=7, rol="cliente"))

    assert payload["sub"] == "7"
    assert payload["rol"] == "cliente"
    assert "exp" in payload


def test_vencido():
    token = crear_token(id_usuario=7, rol="cliente", expira_minutos=-1)

    with pytest.raises(ValueError, match="vencido"):
        decodificar_token(token)


def falsificado() -> str:
    return jwt.encode({"sub": "1", "rol": "repartidor"}, "una_clave_que_no_es_la_nuestra_123456789",
                      algorithm=settings.jwt_algoritmo)


def alterado() -> str:
    header, payload, firma = crear_token(id_usuario=7, rol="cliente").split(".")
    return f"{header}.{payload}.{firma[:5]}{'B' if firma[5] == 'A' else 'A'}{firma[6:]}"


@pytest.mark.parametrize("token", [falsificado(), alterado(), "hola"])
def test_invalido(token):
    with pytest.raises(ValueError, match="inválido"):
        decodificar_token(token)
