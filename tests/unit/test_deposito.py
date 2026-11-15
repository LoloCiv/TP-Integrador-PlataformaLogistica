from app.models import Deposito, Producto


# El depósito lista los productos que tiene asociados
def test_listar_productos():
    deposito = Deposito(nombre="Depósito Central", direccion="Calle Falsa 123")

    producto1 = Producto(nombre="Producto 1", deposito=deposito)
    producto2 = Producto(nombre="Producto 2", deposito=deposito)

    assert deposito.listar_productos() == [producto1, producto2]
