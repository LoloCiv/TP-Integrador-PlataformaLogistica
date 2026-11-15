from decimal import Decimal

import pytest

from app.models import DetalleOrden, Inventario, Orden

# Todos los tests del archivo son async
pytestmark = pytest.mark.anyio

# Datos de un cliente de prueba
ANA = {"nombre": "Ana", "apellido": "Paz", "user_name": "ana", "password": "secreta123",
       "direccion": "Malabia 100", "telefono": "1144556677", "dni": "30111222"}


# Crea el cliente, hace login y devuelve su id y el header con el token
async def registrar_y_login(cliente, datos=ANA):
    respuesta = await cliente.post("/clientes", json=datos)
    token = (await cliente.post("/auth/login", json={"user_name": datos["user_name"],
                                                      "password": datos["password"]})).json()["data"]["access_token"]
    return respuesta.json()["data"]["id_usuario"], {"Authorization": f"Bearer {token}"}


# Crea un depósito, un producto y su inventario
async def cargar_catalogo(cliente, headers, stock=100):
    await cliente.post("/depositos", headers=headers,
                       json={"nombre": "Central", "direccion": "A", "latitud": -34.6, "longitud": -58.4})
    respuesta = await cliente.post("/productos", headers=headers,
                           json={"id_deposito": 1, "nombre": "Dulce", "precio": 100, "peso": 1, "categoria": "a"})
    id_producto = respuesta.json()["data"]["id_producto"]
    await cliente.post("/inventario", headers=headers, json={"id_producto": id_producto, "stock_actual": stock})
    return id_producto


# Body de una orden con un solo producto
def orden(id_producto, cantidad):
    return {"direccion_entrega": "Malabia 100", "latitud": -34.59, "longitud": -58.42,
            "detalles": [{"id_producto": id_producto, "cantidad": cantidad}]}


# /health responde y confirma que la base está conectada
async def test_health(cliente):
    respuesta = await cliente.get("/health")

    assert respuesta.json() == {"status": 200, "data": {"api": "ok", "db": "ok"}}


# Login correcto devuelve el token con el rol; con la contraseña mal, 401
async def test_login(cliente):
    await cliente.post("/clientes", json=ANA)

    ok = await cliente.post("/auth/login", json={"user_name": "ana", "password": "secreta123"})
    mal = await cliente.post("/auth/login", json={"user_name": "ana", "password": "otra"})

    assert ok.status_code == 200
    assert ok.json()["data"]["rol"] == "cliente"
    assert mal.status_code == 401


# POST /ordenes guarda la orden y el detalle, y descuenta el stock en Postgres
async def test_crear_orden(cliente, db):
    _, headers = await registrar_y_login(cliente)
    id_producto = await cargar_catalogo(cliente, headers, stock=100)

    respuesta = await cliente.post("/ordenes", headers=headers, json=orden(id_producto, 30))

    assert respuesta.status_code == 201
    id_orden = respuesta.json()["data"]["id_orden"]
    guardada = db.get(Orden, id_orden)
    assert guardada.total == Decimal("3000")
    assert db.query(DetalleOrden).filter_by(id_orden=id_orden).count() == 1
    assert db.query(Inventario).filter_by(id_producto=id_producto).one().stock_actual == 70


# Ana ve su historial; otro cliente que pide el de Ana recibe 403
async def test_historial(cliente):
    id_ana, headers_ana = await registrar_y_login(cliente)
    id_producto = await cargar_catalogo(cliente, headers_ana)
    await cliente.post("/ordenes", headers=headers_ana, json=orden(id_producto, 1))
    await cliente.post("/ordenes", headers=headers_ana, json=orden(id_producto, 2))
    _, headers_beto = await registrar_y_login(cliente, {**ANA, "user_name": "beto", "dni": "30111223"})

    propio = await cliente.get(f"/clientes/{id_ana}/ordenes", headers=headers_ana)
    ajeno = await cliente.get(f"/clientes/{id_ana}/ordenes", headers=headers_beto)

    assert propio.status_code == 200
    assert propio.json()["paginacion"]["total"] == 2
    assert ajeno.status_code == 403


# Dos órdenes asignadas a Juan quedan en la misma ruta. Un cliente no puede iniciarla (403);
# Juan sí, y las dos pasan a EN_CAMINO
async def test_iniciar_ruta(cliente):
    _, headers_ana = await registrar_y_login(cliente)
    id_producto = await cargar_catalogo(cliente, headers_ana)
    juan = (await cliente.post("/repartidores", headers=headers_ana, json={
        "nombre": "Juan", "apellido": "Gil", "user_name": "juan", "password": "secreta123",
        "legajo": "R1", "sueldo": 1000, "licencia": "L1"})).json()["data"]["id_usuario"]
    vehiculo = (await cliente.post("/vehiculos", headers=headers_ana, json={
        "patente": "AA111BB", "marca": "Fiat", "modelo": "Fiorino", "tipo_vehiculo": "CAMIONETA",
        "capacidad_kg": 100, "id_repartidor": juan})).json()["data"]["id_vehiculo"]
    ids = []
    for cantidad in (1, 2):
        id_orden = (await cliente.post("/ordenes", headers=headers_ana, json=orden(id_producto, cantidad))).json()["data"]["id_orden"]
        respuesta = await cliente.patch(f"/ordenes/{id_orden}/asignar", headers=headers_ana,
                                json={"id_repartidor": juan, "id_vehiculo": vehiculo})
        ids.append(id_orden)
    id_ruta = respuesta.json()["data"]["id_ruta"]
    token_juan = (await cliente.post("/auth/login", json={"user_name": "juan", "password": "secreta123"})).json()["data"]["access_token"]
    headers_juan = {"Authorization": f"Bearer {token_juan}"}

    como_cliente = await cliente.patch(f"/rutas/{id_ruta}/iniciar", headers=headers_ana)
    como_repartidor = await cliente.patch(f"/rutas/{id_ruta}/iniciar", headers=headers_juan)

    assert como_cliente.status_code == 403
    assert como_repartidor.status_code == 200
    salieron = como_repartidor.json()["data"]
    assert sorted(salida["id_orden"] for salida in salieron) == sorted(ids)
    assert all(salida["estado_orden"] == "EN_CAMINO" for salida in salieron)
