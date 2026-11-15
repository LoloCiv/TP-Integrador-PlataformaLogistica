import pytest

from app.models import Repartidor
from app.models.enums import EstadoRepartidor


def test_cambiar_estado():
    repartidor = Repartidor(estado_repartidor=EstadoRepartidor.DISPONIBLE)
    assert repartidor.esta_disponible() is True

    repartidor.cambiar_estado(EstadoRepartidor.EN_RUTA)

    assert repartidor.estado_repartidor == EstadoRepartidor.EN_RUTA
    assert repartidor.esta_disponible() is False


def test_estado_invalido():
    repartidor = Repartidor(estado_repartidor=EstadoRepartidor.DISPONIBLE)

    with pytest.raises(ValueError):
        repartidor.cambiar_estado("INVALIDO")

    assert repartidor.estado_repartidor == EstadoRepartidor.DISPONIBLE
