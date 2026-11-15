import pytest

from app.models import Repartidor
from app.models.enums import EstadoRepartidor


# Al pasar a EN_RUTA deja de estar disponible
def test_cambiar_estado():
    repartidor = Repartidor(estado_repartidor=EstadoRepartidor.DISPONIBLE)
    assert repartidor.esta_disponible() is True

    repartidor.cambiar_estado(EstadoRepartidor.EN_RUTA)

    assert repartidor.estado_repartidor == EstadoRepartidor.EN_RUTA
    assert repartidor.esta_disponible() is False


# Un estado que no existe da error y no cambia nada
def test_estado_invalido():
    repartidor = Repartidor(estado_repartidor=EstadoRepartidor.DISPONIBLE)

    with pytest.raises(ValueError):
        repartidor.cambiar_estado("INVALIDO")

    assert repartidor.estado_repartidor == EstadoRepartidor.DISPONIBLE
