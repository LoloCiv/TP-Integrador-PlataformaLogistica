from decimal import Decimal

import pytest
from app.models import TrackingUbicacion


def crear_tracking() -> TrackingUbicacion:
    return TrackingUbicacion(latitud=Decimal("-34.600000"), longitud=Decimal("-58.400000"))


def test_actualizar_posicion():
    tracking = crear_tracking()

    tracking.actualizar_posicion(Decimal("-31.420000"), Decimal("-64.180000"))

    assert tracking.latitud == Decimal("-31.420000")
    assert tracking.longitud == Decimal("-64.180000")

@pytest.mark.parametrize("latitud, longitud", [
    (Decimal("90.1"), Decimal("0")),
    (Decimal("-91"), Decimal("0")),
    (Decimal("0"), Decimal("180.5")),
    (Decimal("0"), Decimal("-181")),
])
def test_actualizar_posicion_invalida(latitud, longitud):
    tracking = crear_tracking()

    with pytest.raises(ValueError):
        tracking.actualizar_posicion(latitud, longitud)

    assert tracking.latitud == Decimal("-34.600000")
    assert tracking.longitud == Decimal("-58.400000")
