import time
from uuid import uuid4

import httpx
import pytest

URL = "http://localhost:8000"


def test_flujo():
    sufijo = uuid4().hex[:8]
    cliente_http = httpx.Client(base_url=URL, timeout=10)
    try:
        cliente_http.get("/health")
    except httpx.ConnectError:
        pytest.skip("El backend no está levantado")

    def post(ruta, **kwargs):
        respuesta = cliente_http.post(ruta, **kwargs)
        respuesta.raise_for_status()
        return respuesta.json()["data"]

    dni = str(uuid4().int)[:8]
    post("/clientes", json={"nombre": "Ana", "apellido": "Paz", "user_name": f"ana{sufijo}", "password": "secreta123",
                            "direccion": "Malabia 100", "telefono": "1144556677", "dni": dni})
    token = post("/auth/login", json={"user_name": f"ana{sufijo}", "password": "secreta123"})["access_token"]
    cliente_http.headers["Authorization"] = f"Bearer {token}"

    id_deposito = post("/depositos", json={"nombre": f"D{sufijo}", "direccion": "A", "latitud": -34.6, "longitud": -58.4})["id_deposito"]
    id_producto = post("/productos", json={"id_deposito": id_deposito, "nombre": f"P{sufijo}", "precio": 100,
                                           "peso": 1, "categoria": "a"})["id_producto"]
    post("/inventario", json={"id_producto": id_producto, "stock_actual": 10})
    id_repartidor = post("/repartidores", json={"nombre": "Beto", "apellido": "Ruiz", "user_name": f"beto{sufijo}",
                                                "password": "secreta123", "legajo": sufijo, "sueldo": 1000,
                                                "licencia": sufijo})["id_usuario"]
    id_vehiculo = post("/vehiculos", json={"patente": f"E{sufijo}", "marca": "Fiat", "modelo": "Fiorino",
                                           "tipo_vehiculo": "CAMIONETA", "capacidad_kg": 100,
                                           "id_repartidor": id_repartidor})["id_vehiculo"]

    id_orden = post("/ordenes", json={"direccion_entrega": "Malabia 100", "latitud": -34.59, "longitud": -58.42,
                                      "detalles": [{"id_producto": id_producto, "cantidad": 1}]})["id_orden"]
    assert cliente_http.get(f"/ordenes/{id_orden}").json()["data"]["nro_parada"] is None

    respuesta = cliente_http.patch(f"/ordenes/{id_orden}/asignar", json={"id_repartidor": id_repartidor, "id_vehiculo": id_vehiculo})
    respuesta.raise_for_status()

    nro_parada = None
    for _ in range(20):
        nro_parada = cliente_http.get(f"/ordenes/{id_orden}").json()["data"]["nro_parada"]
        if nro_parada is not None:
            break
        time.sleep(0.5)

    assert nro_parada == 1
