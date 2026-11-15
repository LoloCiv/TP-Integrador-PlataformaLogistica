from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencias import requiere_rol, usuario_actual
from app.core.respuestas import Paginacion, respuesta_ok, respuesta_paginada
from app.db import get_db
from app.models import Orden, Usuario
from app.schemas.orden import AsignarRepartidorEntrada, CambiarEstadoEntrada, OrdenCrear, OrdenSalida
from app.services.cola_mensajes import ColaRedis
from app.services.gestor_pedidos import GestorPedidos

router = APIRouter(prefix="/ordenes", tags=["Ordenes"])


# Arma el gestor con la sesión y la cola de Redis. En los tests se reemplaza por uno con ColaFalsa
def obtener_gestor(db: Session = Depends(get_db)) -> GestorPedidos:
    return GestorPedidos(db, ColaRedis())


# Solo clientes. La lógica está en el gestor
@router.post("", dependencies=[Depends(requiere_rol("cliente"))])
def crear_orden(
    datos: OrdenCrear,
    usuario: Usuario = Depends(usuario_actual),
    gestor: GestorPedidos = Depends(obtener_gestor),
):
    orden = gestor.crear_orden(usuario, datos)
    return respuesta_ok(OrdenSalida.model_validate(orden), status=201)


@router.get("")
def listar_ordenes(pag: Paginacion = Depends(), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Orden))
    ordenes = db.scalars(
        select(Orden).order_by(Orden.id_orden).offset(pag.offset).limit(pag.limit)
    ).all()
    items = [OrdenSalida.model_validate(orden) for orden in ordenes]
    return respuesta_paginada(items, total, pag.limit, pag.offset)


@router.get("/{id_orden}")
def ver_orden(id_orden: int, gestor: GestorPedidos = Depends(obtener_gestor)):
    orden = gestor.get_orden_by_id(id_orden)
    return respuesta_ok(OrdenSalida.model_validate(orden))


# Pasa la orden a CONFIRMADA y manda a calcular la ruta
@router.patch("/{id_orden}/asignar")
def asignar_repartidor(
    id_orden: int,
    datos: AsignarRepartidorEntrada,
    gestor: GestorPedidos = Depends(obtener_gestor),
):
    orden = gestor.asignar_repartidor(id_orden, datos.id_repartidor, datos.id_vehiculo)
    return respuesta_ok(OrdenSalida.model_validate(orden))


# Hoy solo sirve para marcar ENTREGADA (ver TRANSICIONES). Solo el repartidor de la ruta de la orden
@router.patch("/{id_orden}/estado", dependencies=[Depends(requiere_rol("repartidor"))])
def cambiar_estado(
    id_orden: int,
    datos: CambiarEstadoEntrada,
    usuario: Usuario = Depends(usuario_actual),
    gestor: GestorPedidos = Depends(obtener_gestor),
):
    orden = gestor.actualizar_estado(id_orden, datos.estado_orden, usuario.id_usuario)
    return respuesta_ok(OrdenSalida.model_validate(orden))


# Cancela y devuelve el stock
@router.patch("/{id_orden}/cancelar")
def cancelar_orden(id_orden: int, gestor: GestorPedidos = Depends(obtener_gestor)):
    orden = gestor.cancelar_orden(id_orden)
    return respuesta_ok(OrdenSalida.model_validate(orden))
