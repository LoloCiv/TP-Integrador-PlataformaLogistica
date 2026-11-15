from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Usuario


# Trae de la base el usuario del token (AuthMiddleware ya dejó sus datos en request.state)
def usuario_actual(request: Request, db: Session = Depends(get_db)) -> Usuario:
    id_usuario = int(request.state.usuario["sub"])

    usuario = db.get(Usuario, id_usuario)
    if usuario is None:
        raise HTTPException(status_code=401, detail="El usuario del token ya no existe")

    return usuario


# Devuelve una dependencia que corta con 403 si el rol del token no es uno de los permitidos
def requiere_rol(*roles: str):

    def verificar(request: Request) -> None:
        if request.state.usuario["rol"] not in roles:
            raise HTTPException(status_code=403, detail="No tenés permiso para esta acción")
    return verificar
