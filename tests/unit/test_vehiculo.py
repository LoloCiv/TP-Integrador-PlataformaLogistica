import pytest

from app.models import Vehiculo
from app.models.enums import EstadoVehiculo


# Al pasar a MANTENIMIENTO deja de estar disponible
def test_cambiar_estado():
    vehiculo = Vehiculo(estado_vehiculo=EstadoVehiculo.DISPONIBLE)
    assert vehiculo.esta_disponible() is True

    vehiculo.cambiar_estado(EstadoVehiculo.MANTENIMIENTO)

    assert vehiculo.estado_vehiculo == EstadoVehiculo.MANTENIMIENTO
    assert vehiculo.esta_disponible() is False


# Un estado que no existe da error y no cambia nada
def test_estado_invalido():
    vehiculo = Vehiculo(estado_vehiculo=EstadoVehiculo.DISPONIBLE)

    with pytest.raises(ValueError):
        vehiculo.cambiar_estado("INVALIDO")

    assert vehiculo.estado_vehiculo == EstadoVehiculo.DISPONIBLE
