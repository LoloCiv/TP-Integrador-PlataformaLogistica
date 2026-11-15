from decimal import Decimal

from app.models import DetalleOrden, Orden, Producto


def test_total():
    orden = Orden(direccion_entrega="Calle 1")
    assert orden.calcular_total() == Decimal("0")

    orden.agregar_detalle(DetalleOrden(cantidad=2, precio_unitario=Decimal("10")))
    orden.agregar_detalle(DetalleOrden(cantidad=3, precio_unitario=Decimal("5")))

    assert orden.total == Decimal("35")


def test_remover():
    orden = Orden(direccion_entrega="Calle 1")
    detalle1 = DetalleOrden(cantidad=2, precio_unitario=Decimal("10"))
    detalle2 = DetalleOrden(cantidad=1, precio_unitario=Decimal("5"))
    orden.agregar_detalle(detalle1)
    orden.agregar_detalle(detalle2)

    orden.remover_detalle(detalle1)

    assert detalle1 not in orden.detalles
    assert orden.total == Decimal("5")


def test_peso():
    orden = Orden(direccion_entrega="Calle 1")
    harina = Producto(nombre="Harina", peso=Decimal("1.5"), precio=Decimal("10"))
    yerba = Producto(nombre="Yerba", peso=Decimal("0.5"), precio=Decimal("20"))
    orden.agregar_detalle(DetalleOrden(cantidad=2, precio_unitario=Decimal("10"), producto=harina))
    orden.agregar_detalle(DetalleOrden(cantidad=4, precio_unitario=Decimal("20"), producto=yerba))

    assert orden.calcular_peso() == Decimal("5")
