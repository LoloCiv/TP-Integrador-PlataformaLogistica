import pytest

from app.models import Inventario


# Consulta el stock y si alcanza para una cantidad (el límite exacto alcanza)
def test_hay_stock():
    inv = Inventario(stock_actual=10)

    assert inv.consultar_stock() == 10
    assert inv.hay_stock_suficiente(10) is True
    assert inv.hay_stock_suficiente(11) is False


# Descontar resta del stock actual
def test_descontar():
    inv = Inventario(stock_actual=10)

    inv.descontar_stock(3)

    assert inv.stock_actual == 7


# Más que el stock, cero o negativo: error, y el stock no cambia
@pytest.mark.parametrize("cantidad", [11, 0, -5])
def test_descontar_invalido(cantidad):
    inv = Inventario(stock_actual=10)

    with pytest.raises(ValueError):
        inv.descontar_stock(cantidad)

    assert inv.stock_actual == 10
