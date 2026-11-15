from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencias import requiere_rol, usuario_actual
from app.core.respuestas import respuesta_ok
from app.core.security import decodificar_token
from app.db import get_db
from app.models import Orden, Repartidor, Ruta, TrackingUbicacion
from app.models.enums import EstadoOrden
from app.schemas.tracking import PosicionEntrada, TrackingSalida
from app.services.conexiones import GestorConexiones

router = APIRouter(prefix="/tracking", tags=["Tracking"])

# Uno solo para toda la app: guarda quién mira cada orden
conexiones = GestorConexiones()


# Las órdenes EN_CAMINO del repartidor: a esas se les manda su posición
def ordenes_activas(db: Session, id_repartidor: int) -> list[int]:
    return db.scalars(
        select(Orden.id_orden)
        .join(Orden.ruta)
        .where(
            Ruta.id_repartidor == id_repartidor,
            Orden.estado_orden == EstadoOrden.EN_CAMINO,
        )
    ).all()


# Token válido; si es cliente, que la orden sea suya; si es repartidor, que esté en una ruta suya
def validar_acceso(db: Session, token: str, id_orden: int) -> bool:
    try:
        payload = decodificar_token(token)
    except ValueError:
        return False
    orden = db.get(Orden, id_orden)
    if orden is None:
        return False
    if payload["rol"] == "cliente":
        return orden.id_cliente == int(payload["sub"])
    if payload["rol"] == "repartidor":
        return orden.ruta is not None and orden.ruta.id_repartidor == int(payload["sub"])
    return True


# El repartidor manda su posición: se guarda y se reenvía a quienes miran sus órdenes en camino
@router.put("", dependencies=[Depends(requiere_rol("repartidor"))])
async def actualizar_mi_posicion(
    datos: PosicionEntrada,
    usuario: Repartidor = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    tracking = usuario.tracking_ubicacion
    if tracking is None:
        tracking = TrackingUbicacion(repartidor=usuario, latitud=datos.latitud, longitud=datos.longitud)
        db.add(tracking)
    else:
        tracking.actualizar_posicion(datos.latitud, datos.longitud)
    db.commit()
    db.refresh(tracking)
    salida = TrackingSalida.model_validate(tracking)
    for id_orden in ordenes_activas(db, usuario.id_repartidor):
        await conexiones.enviar(id_orden, salida.model_dump(mode="json"))
    return respuesta_ok(salida)


# Conexión que queda abierta mientras alguien mira la orden. Si no tiene acceso se cierra con 1008
@router.websocket("/{id_orden}")
async def seguir_orden(
    websocket: WebSocket,
    id_orden: int,
    token: str = Query(),
    db: Session = Depends(get_db),
):
    if not validar_acceso(db, token, id_orden):
        await websocket.close(code=1008)
        return
    await conexiones.conectar(id_orden, websocket)
    try:
        # Solo mantiene viva la conexión; los datos los manda el PUT
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        conexiones.desconectar(id_orden, websocket)
