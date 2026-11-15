from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Cliente, Deposito, Inventario, Producto, Repartidor, Vehiculo
from app.models.enums import EstadoOrden as E
from app.schemas.orden import OrdenCrear
from app.services.cola_mensajes import ColaMensajes
from app.services.gestor_pedidos import GestorPedidos


# Cola de prueba: guarda los mensajes en una lista en vez de mandarlos a Redis
class ColaFalsa(ColaMensajes):
    def __init__(self):
        self.mensajes = []

    def publicar(self, mensaje):
        self.mensajes.append(mensaje)


# Base SQLite en memoria, nueva para cada test
@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sesion = sessionmaker(bind=engine)()
    yield sesion
    sesion.close()


# Una cola falsa por test, para revisar qué se publicó
@pytest.fixture
def cola():
    return ColaFalsa()


# El gestor real con la base de prueba y la cola falsa (inyección de dependencias)
@pytest.fixture
def gestor(db, cola):
    return GestorPedidos(db, cola)


# Datos de base: dos depósitos con un producto cada uno, tres repartidores (uno INACTIVO)
# y una moto de 20 kg y una camioneta de 600 kg, las dos de Juan
@pytest.fixture
def escenario(db):
    central = Deposito(nombre="Central", direccion="A", latitud=Decimal("-34.6"), longitud=Decimal("-58.4"))
    norte = Deposito(nombre="Norte", direccion="B", latitud=Decimal("-34.5"), longitud=Decimal("-58.5"))

    def producto(nombre, deposito, stock):
        return Producto(nombre=nombre, precio=Decimal("100"), peso=Decimal("1"), categoria="a",
                        deposito=deposito, inventario=Inventario(stock_actual=stock))

    def repartidor(user, estado="DISPONIBLE"):
        return Repartidor(nombre=user, apellido="X", user_name=user, password="x", legajo=user,
                          sueldo=Decimal(1), licencia=user, estado_repartidor=estado)

    def vehiculo(patente, capacidad, dueno):
        return Vehiculo(patente=patente, marca="M", modelo="M", tipo_vehiculo="AUTO",
                        capacidad_kg=Decimal(capacidad), estado_vehiculo="DISPONIBLE", repartidor=dueno)

    juan, beto = repartidor("juan"), repartidor("beto")
    datos = SimpleNamespace(
        cliente=Cliente(nombre="Ana", apellido="P", user_name="ana", password="x",
                        direccion="M", telefono="1144556677", dni="30111222"),
        dulce=producto("Dulce", central, 100),
        harina=producto("Harina", norte, 10),
        juan=juan, beto=beto, inactivo=repartidor("inactivo", "INACTIVO"),
        moto=vehiculo("AA111BB", "20", juan),
        camioneta=vehiculo("CC222DD", "600", juan),
    )
    db.add_all([datos.cliente, datos.dulce, datos.harina, datos.moto, datos.camioneta, datos.beto, datos.inactivo])
    db.commit()
    return datos


# Arma el body de una orden a partir de pares (producto, cantidad)
def pedido(*items, latitud="-34.59", longitud="-58.42"):
    return OrdenCrear(direccion_entrega="x", latitud=Decimal(latitud), longitud=Decimal(longitud),
                      detalles=[{"id_producto": producto.id_producto, "cantidad": cantidad} for producto, cantidad in items])


# Crear una orden calcula el total, la deja PENDIENTE y descuenta el stock
def test_crear_orden(gestor, escenario):
    orden = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 50)))

    assert orden.estado_orden == E.PENDIENTE
    assert orden.total == Decimal("5000")
    assert escenario.dulce.inventario.stock_actual == 50


# El detalle guarda el precio del momento: si después cambia el del producto, la orden no cambia
def test_foto_precio(gestor, escenario, db):
    orden = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 10)))

    escenario.dulce.actualizar_precio(Decimal("150"))
    db.commit()

    assert orden.detalles[0].precio_unitario == Decimal("100")


# Productos de distintos depósitos o sin stock suficiente: error, y el stock queda igual
def test_reglas(gestor, escenario):
    with pytest.raises(ValueError, match="mismo depósito"):
        gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 1), (escenario.harina, 1)))
    with pytest.raises(ValueError, match="stock suficiente"):
        gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 999)))

    assert escenario.dulce.inventario.stock_actual == 100


# No se puede saltear estados: PENDIENTE → CONFIRMADA → EN_CAMINO → ENTREGADA.
# Una orden entregada ya no se puede cancelar
def test_flujo_estados(gestor, escenario):
    orden = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 1)))
    with pytest.raises(ValueError):
        gestor.actualizar_estado(orden.id_orden, E.EN_CAMINO)

    gestor.asignar_repartidor(orden.id_orden, escenario.juan.id_repartidor, escenario.camioneta.id_vehiculo)
    with pytest.raises(ValueError):
        gestor.actualizar_estado(orden.id_orden, E.EN_CAMINO)
    gestor.iniciar_ruta(orden.id_ruta, escenario.juan.id_repartidor)
    gestor.actualizar_estado(orden.id_orden, E.ENTREGADA)

    assert orden.estado_orden == E.ENTREGADA
    assert orden.fecha_entrega is not None
    with pytest.raises(ValueError):
        gestor.cancelar_orden(orden.id_orden)


# Cancelar devuelve el stock. Cancelar dos veces falla y no lo devuelve de nuevo
def test_cancelar(gestor, escenario):
    orden = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 30)))

    gestor.cancelar_orden(orden.id_orden)

    assert orden.estado_orden == E.CANCELADA
    assert escenario.dulce.inventario.stock_actual == 100
    with pytest.raises(ValueError):
        gestor.cancelar_orden(orden.id_orden)
    assert escenario.dulce.inventario.stock_actual == 100


# Una orden EN_CAMINO no se puede cancelar y el stock sigue descontado
def test_cancelar_en_camino(gestor, escenario):
    orden = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 30)))
    gestor.asignar_repartidor(orden.id_orden, escenario.juan.id_repartidor, escenario.camioneta.id_vehiculo)
    gestor.iniciar_ruta(orden.id_ruta, escenario.juan.id_repartidor)

    with pytest.raises(ValueError):
        gestor.cancelar_orden(orden.id_orden)

    assert orden.estado_orden == E.EN_CAMINO
    assert escenario.dulce.inventario.stock_actual == 70


# Asignar confirma la orden y publica un mensaje: primero el depósito y después la entrega
def test_asignar(gestor, cola, escenario):
    orden = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 10)))

    gestor.asignar_repartidor(orden.id_orden, escenario.juan.id_repartidor, escenario.camioneta.id_vehiculo)

    assert orden.estado_orden == E.CONFIRMADA
    assert len(cola.mensajes) == 1
    assert cola.mensajes[0].orden_ids == [orden.id_orden]
    paradas = [(parada.latitud, parada.longitud) for parada in cola.mensajes[0].paradas]
    assert paradas == [(-34.6, -58.4), (-34.59, -58.42)]


# Dos órdenes con el mismo repartidor y vehículo van a la misma ruta, que se republica con las dos
def test_misma_ruta(gestor, cola, escenario):
    orden_1 = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 1)))
    orden_2 = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 1), latitud="-34.62"))

    gestor.asignar_repartidor(orden_1.id_orden, escenario.juan.id_repartidor, escenario.camioneta.id_vehiculo)
    gestor.asignar_repartidor(orden_2.id_orden, escenario.juan.id_repartidor, escenario.camioneta.id_vehiculo)

    assert orden_1.id_ruta == orden_2.id_ruta
    assert cola.mensajes[-1].orden_ids == [orden_1.id_orden, orden_2.id_orden]


# Capacidad superada, repartidor no disponible o vehículo de otro repartidor:
# error, la orden sigue PENDIENTE y no se publica nada
@pytest.mark.parametrize("repartidor, vehiculo, error", [
    ("juan", "moto", "capacidad"),
    ("inactivo", "camioneta", "disponible"),
    ("beto", "camioneta", "no pertenece"),
])
def test_asignar_invalido(gestor, cola, escenario, repartidor, vehiculo, error):
    orden = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 50)))

    with pytest.raises(ValueError, match=error):
        gestor.asignar_repartidor(orden.id_orden, getattr(escenario, repartidor).id_repartidor,
                                  getattr(escenario, vehiculo).id_vehiculo)

    assert orden.estado_orden == E.PENDIENTE
    assert cola.mensajes == []


# Iniciar saca juntas las órdenes CONFIRMADA de la ruta y ocupa al repartidor y al vehículo.
# Mientras está EN_RUTA no puede salir con otra ruta. Al entregar la última quedan libres,
# y una orden nueva ya arma otra ruta
def test_iniciar_ruta(gestor, escenario):
    orden_1 = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 1)))
    orden_2 = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 1), latitud="-34.62"))
    en_moto = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 1)))
    gestor.asignar_repartidor(orden_1.id_orden, escenario.juan.id_repartidor, escenario.camioneta.id_vehiculo)
    gestor.asignar_repartidor(orden_2.id_orden, escenario.juan.id_repartidor, escenario.camioneta.id_vehiculo)
    gestor.asignar_repartidor(en_moto.id_orden, escenario.juan.id_repartidor, escenario.moto.id_vehiculo)

    salieron = gestor.iniciar_ruta(orden_1.id_ruta, escenario.juan.id_repartidor)

    assert {orden.id_orden for orden in salieron} == {orden_1.id_orden, orden_2.id_orden}
    assert orden_1.estado_orden == E.EN_CAMINO and orden_2.estado_orden == E.EN_CAMINO
    assert escenario.juan.estado_repartidor == "EN_RUTA" and escenario.camioneta.estado_vehiculo == "EN_USO"
    with pytest.raises(ValueError, match="no está disponible"):
        gestor.iniciar_ruta(en_moto.id_ruta, escenario.juan.id_repartidor)

    gestor.actualizar_estado(orden_1.id_orden, E.ENTREGADA)
    assert escenario.juan.estado_repartidor == "EN_RUTA"
    gestor.actualizar_estado(orden_2.id_orden, E.ENTREGADA)
    assert escenario.juan.estado_repartidor == "DISPONIBLE" and escenario.camioneta.estado_vehiculo == "DISPONIBLE"

    orden_3 = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 1)))
    gestor.asignar_repartidor(orden_3.id_orden, escenario.juan.id_repartidor, escenario.camioneta.id_vehiculo)
    assert orden_3.id_ruta != orden_1.id_ruta


# Otro repartidor no puede iniciar la ruta, y una ruta que ya salió no se inicia de nuevo
def test_iniciar_ruta_invalida(gestor, escenario):
    orden = gestor.crear_orden(escenario.cliente, pedido((escenario.dulce, 1)))
    gestor.asignar_repartidor(orden.id_orden, escenario.juan.id_repartidor, escenario.camioneta.id_vehiculo)

    with pytest.raises(ValueError, match="no es del repartidor"):
        gestor.iniciar_ruta(orden.id_ruta, escenario.beto.id_repartidor)
    assert orden.estado_orden == E.CONFIRMADA

    gestor.iniciar_ruta(orden.id_ruta, escenario.juan.id_repartidor)
    with pytest.raises(ValueError, match="no tiene órdenes CONFIRMADA"):
        gestor.iniciar_ruta(orden.id_ruta, escenario.juan.id_repartidor)
