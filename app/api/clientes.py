from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.respuestas import Paginacion, respuesta_ok, respuesta_paginada
from app.db import get_db
from app.models import Cliente
from app.schemas.cliente import ClienteActualizar, ClienteCrear, ClienteSalida
from app.schemas.orden import OrdenSalida

router = APIRouter(prefix="/clientes", tags=["Clientes"])


# Busca el cliente o corta con 404
def buscar_cliente(db: Session, id_cliente: int) -> Cliente:
    cliente = db.get(Cliente, id_cliente)
    if cliente is None:
        raise HTTPException(status_code=404, detail=f"Cliente {id_cliente} no existe")
    return cliente


@router.get("")
def listar_clientes(pag: Paginacion = Depends(), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Cliente))
    clientes = db.scalars(
        select(Cliente).order_by(Cliente.id_cliente).offset(pag.offset).limit(pag.limit)
    ).all()
    items = [ClienteSalida.model_validate(cliente) for cliente in clientes]
    return respuesta_paginada(items, total, pag.limit, pag.offset)


@router.get("/{id_cliente}")
def ver_cliente(id_cliente: int, db: Session = Depends(get_db)):
    return respuesta_ok(ClienteSalida.model_validate(buscar_cliente(db, id_cliente)))


# Registro (ruta pública). La contraseña se saca del ** porque se guarda hasheada
@router.post("")
def registrar_cliente(datos: ClienteCrear, db: Session = Depends(get_db)):
    cliente = Cliente(**datos.model_dump(exclude={"password"}))
    cliente.cambiar_password(datos.password)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return respuesta_ok(ClienteSalida.model_validate(cliente), status=201)


# Solo cambia los campos que vinieron en el body (exclude_unset)
@router.patch("/{id_cliente}")
def modificar_cliente(id_cliente: int, datos: ClienteActualizar, db: Session = Depends(get_db)):
    cliente = buscar_cliente(db, id_cliente)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return respuesta_ok(ClienteSalida.model_validate(cliente))


# Un cliente solo puede ver su propio historial
@router.get("/{id_cliente}/ordenes")
def historial(id_cliente: int, request: Request, pag: Paginacion = Depends(), db: Session = Depends(get_db)):
    usuario = request.state.usuario
    if usuario["rol"] == "cliente" and int(usuario["sub"]) != id_cliente:
        raise HTTPException(status_code=403, detail="Solo podés ver tu propio historial")
    ordenes = buscar_cliente(db, id_cliente).historial_ordenes()
    pagina = ordenes[pag.offset : pag.offset + pag.limit]
    items = [OrdenSalida.model_validate(orden) for orden in pagina]
    return respuesta_paginada(items, len(ordenes), pag.limit, pag.offset)
