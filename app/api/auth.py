from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencias import usuario_actual
from app.core.respuestas import respuesta_ok
from app.core.security import crear_token
from app.db import get_db
from app.models import Cliente, Usuario
from app.schemas.auth import CambiarPasswordEntrada, LoginEntrada, TokenSalida
from app.schemas.cliente import ClienteSalida
from app.schemas.repartidor import RepartidorSalida

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# Valida usuario y contraseña y devuelve un token con el rol
@router.post("/login")
def login(datos: LoginEntrada, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.user_name == datos.user_name))

    if not usuario or not usuario.validar_credenciales(datos.password, datos.user_name):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = crear_token(usuario.id_usuario, usuario.tipo)
    return respuesta_ok(TokenSalida(access_token=token, rol=usuario.tipo))


# Datos del usuario logueado, con el schema que corresponde a su tipo
@router.get("/yo")
def ver_mis_datos(usuario: Usuario = Depends(usuario_actual)):
    if isinstance(usuario, Cliente):
        datos = ClienteSalida.model_validate(usuario)
    else:
        datos = RepartidorSalida.model_validate(usuario)
    return respuesta_ok(datos)


# Cambia la contraseña verificando primero la actual
@router.patch("/password")
def cambiar_mi_password(
    datos: CambiarPasswordEntrada,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    if not usuario.validar_credenciales(datos.password_actual, usuario.user_name):
        raise HTTPException(status_code=401, detail="La contraseña actual no es correcta")

    usuario.cambiar_password(datos.password_nueva)
    db.commit()
    return respuesta_ok({"mensaje": "Contraseña actualizada"})
