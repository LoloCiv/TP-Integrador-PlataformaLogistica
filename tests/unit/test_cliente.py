from app.models import Cliente, Orden


# El historial devuelve las órdenes del cliente en el orden en que se agregaron
def test_historial():
    cliente = Cliente(direccion="Malabia", telefono="123456789", dni="12345678")
    assert cliente.historial_ordenes() == []

    orden1 = Orden(direccion_entrega="Calle 1")
    orden2 = Orden(direccion_entrega="Calle 2")
    cliente.ordenes.append(orden1)
    cliente.ordenes.append(orden2)

    assert cliente.historial_ordenes() == [orden1, orden2]
