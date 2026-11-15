from fastapi import APIRouter, Depends

from app.api.ordenes import obtener_gestor
from app.core.dependencias import requiere_rol, usuario_actual
from app.core.respuestas import respuesta_ok
from app.models import Usuario
from app.schemas.orden import OrdenSalida
from app.services.gestor_pedidos import GestorPedidos

router = APIRouter(prefix="/rutas", tags=["Rutas"])


# El repartidor arranca su ruta: todas sus órdenes confirmadas pasan a EN_CAMINO
@router.patch("/{id_ruta}/iniciar", dependencies=[Depends(requiere_rol("repartidor"))])
def iniciar_ruta(
    id_ruta: int,
    usuario: Usuario = Depends(usuario_actual),
    gestor: GestorPedidos = Depends(obtener_gestor),
):
    ordenes = gestor.iniciar_ruta(id_ruta, usuario.id_usuario)
    return respuesta_ok([OrdenSalida.model_validate(orden) for orden in ordenes])
