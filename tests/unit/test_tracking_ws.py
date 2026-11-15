from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.websockets import WebSocketDisconnect

from app.core.security import crear_token
from app.db import Base, get_db
from app.main import app
from app.models import Cliente, Orden, Repartidor, Ruta, Vehiculo

ids = {}


@pytest.fixture
def cliente_http():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Sesion = sessionmaker(bind=engine)

    def db_prueba():
        db = Sesion()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = db_prueba

    db = Sesion()
    usuarios = {}
    for nombre_cliente, nombre_repartidor, dni in [("ana", "juan", "30111222"), ("beto", "pedro", "30111223")]:
        cliente = Cliente(nombre=nombre_cliente, apellido="P", user_name=nombre_cliente, password="x", direccion="M", telefono="1144556677", dni=dni)
        repartidor = Repartidor(nombre=nombre_repartidor, apellido="G", user_name=nombre_repartidor, password="x", legajo=nombre_repartidor,
                                sueldo=Decimal(1), licencia=nombre_repartidor, estado_repartidor="DISPONIBLE")
        vehiculo = Vehiculo(patente=dni[-7:], marca="F", modelo="F", tipo_vehiculo="AUTO", capacidad_kg=Decimal(100),
                            estado_vehiculo="DISPONIBLE", repartidor=repartidor)
        db.add(Orden(cliente=cliente, ruta=Ruta(repartidor=repartidor, vehiculo=vehiculo), total=Decimal(1),
                     direccion_entrega="x", estado_orden="EN_CAMINO"))
        usuarios[nombre_cliente], usuarios[nombre_repartidor] = cliente, repartidor
    db.commit()
    ids.update({nombre: usuario.id_usuario for nombre, usuario in usuarios.items()})
    ids["orden_ana"] = usuarios["ana"].ordenes[0].id_orden
    db.close()

    yield TestClient(app)
    app.dependency_overrides.clear()


def mirar(cliente_http, quien):
    return cliente_http.websocket_connect(f"/tracking/{ids['orden_ana']}?token={crear_token(ids[quien], 'cliente')}")


def mover(cliente_http, quien, latitud, longitud):
    token = crear_token(ids[quien], "repartidor")
    return cliente_http.put("/tracking", json={"latitud": latitud, "longitud": longitud},
                            headers={"Authorization": f"Bearer {token}"})


def test_recibe_posicion(cliente_http):
    with mirar(cliente_http, "ana") as websocket:
        assert mover(cliente_http, "juan", -34.6, -58.4).status_code == 200

        mensaje = websocket.receive_json()

    assert mensaje["id_repartidor"] == ids["juan"]
    assert Decimal(mensaje["latitud"]) == Decimal("-34.6")


def test_no_filtra(cliente_http):
    with mirar(cliente_http, "ana") as websocket:
        mover(cliente_http, "pedro", -31.4, -64.2)
        mover(cliente_http, "juan", -34.6, -58.4)

        mensaje = websocket.receive_json()

    assert mensaje["id_repartidor"] == ids["juan"]


def test_orden_ajena(cliente_http):
    with pytest.raises(WebSocketDisconnect) as error:
        with mirar(cliente_http, "beto") as websocket:
            websocket.receive_json()

    assert error.value.code == 1008


def test_put_cliente(cliente_http):
    token = crear_token(ids["ana"], "cliente")
    respuesta = cliente_http.put("/tracking", json={"latitud": 0, "longitud": 0}, headers={"Authorization": f"Bearer {token}"})

    assert respuesta.status_code == 403
