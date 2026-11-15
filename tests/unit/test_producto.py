from decimal import Decimal

import pytest

from app.models import Producto


# Actualiza el precio con un valor válido
def test_actualizar_precio():
    producto = Producto(nombre="Producto A", precio=Decimal("10"), peso=Decimal("1"), categoria="Categoria A")

    producto.actualizar_precio(Decimal("15"))

    assert producto.precio == Decimal("15")


# Precio cero o negativo: error, y queda el precio anterior
@pytest.mark.parametrize("precio", [Decimal("0"), Decimal("-5")])
def test_actualizar_precio_invalido(precio):
    producto = Producto(nombre="Producto B", precio=Decimal("20"), peso=Decimal("2"), categoria="Categoria B")

    with pytest.raises(ValueError):
        producto.actualizar_precio(precio)

    assert producto.precio == Decimal("20")
