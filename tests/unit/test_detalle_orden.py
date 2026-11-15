from decimal import Decimal
from app.models import DetalleOrden


def test_calcular_subtotal():
    detalle = DetalleOrden(cantidad=3, precio_unitario=Decimal("10"))

    assert detalle.calcular_subtotal() == Decimal("30")
