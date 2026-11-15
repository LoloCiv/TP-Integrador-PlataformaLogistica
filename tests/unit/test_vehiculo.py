import pytest

from app.models import Vehiculo
from app.models.enums import EstadoVehiculo


def test_cambiar_estado():
    vehiculo = Vehiculo(estado_vehiculo=EstadoVehiculo.DISPONIBLE)
    assert vehiculo.esta_disponible() is True

    vehiculo.cambiar_estado(EstadoVehiculo.MANTENIMIENTO)

    assert vehiculo.estado_vehiculo == EstadoVehiculo.MANTENIMIENTO
    assert vehiculo.esta_disponible() is False


def test_estado_invalido():
    vehiculo = Vehiculo(estado_vehiculo=EstadoVehiculo.DISPONIBLE)

    with pytest.raises(ValueError):
        vehiculo.cambiar_estado("INVALIDO")

    assert vehiculo.estado_vehiculo == EstadoVehiculo.DISPONIBLE
