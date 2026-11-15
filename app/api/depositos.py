from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.respuestas import Paginacion, respuesta_ok, respuesta_paginada
from app.db import get_db
from app.models import Deposito, Producto
from app.schemas.deposito import DepositoActualizar, DepositoCrear, DepositoSalida
from app.schemas.producto import ProductoSalida
router = APIRouter(prefix="/depositos", tags=["Depósitos"])


# Busca el depósito o corta con 404
def buscar_deposito(db: Session, id_deposito: int) -> Deposito:
    deposito = db.get(Deposito, id_deposito)
    if deposito is None:
        raise HTTPException(status_code=404, detail=f"Depósito {id_deposito} no existe")
    return deposito


# Listado paginado: cuenta el total y trae solo la página pedida
@router.get("")
def listar_depositos(pag: Paginacion = Depends(), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Deposito))
    depositos = db.scalars(
        select(Deposito)
        .order_by(Deposito.id_deposito)
        .offset(pag.offset)
        .limit(pag.limit)
    ).all()

    items = [DepositoSalida.model_validate(deposito) for deposito in depositos]
    return respuesta_paginada(items, total, pag.limit, pag.offset)


@router.get("/{id_deposito}")
def ver_deposito(id_deposito: int, db: Session = Depends(get_db)):
    deposito = buscar_deposito(db, id_deposito)
    return respuesta_ok(DepositoSalida.model_validate(deposito))


# Los productos de un depósito, paginados
@router.get("/{id_deposito}/productos")
def listar_productos_del_deposito(
    id_deposito: int, pag: Paginacion = Depends(), db: Session = Depends(get_db)
):
    buscar_deposito(db, id_deposito)
    filtro = Producto.id_deposito == id_deposito
    total = db.scalar(select(func.count()).select_from(Producto).where(filtro))
    productos = db.scalars(
        select(Producto).where(filtro).order_by(Producto.id_producto).offset(pag.offset).limit(pag.limit)
    ).all()
    items = [ProductoSalida.model_validate(producto) for producto in productos]
    return respuesta_paginada(items, total, pag.limit, pag.offset)


# El body coincide con las columnas, así que se pasa directo con **
@router.post("")
def crear_deposito(datos: DepositoCrear, db: Session = Depends(get_db)):
    deposito = Deposito(**datos.model_dump())
    db.add(deposito)
    db.commit()
    db.refresh(deposito)
    return respuesta_ok(DepositoSalida.model_validate(deposito), status=201)


# PUT reemplaza todo (body completo); PATCH cambia solo lo que vino
@router.put("/{id_deposito}")
def reemplazar_deposito(id_deposito: int, datos: DepositoCrear, db: Session = Depends(get_db)):
    deposito = buscar_deposito(db, id_deposito)
    for campo, valor in datos.model_dump().items():
        setattr(deposito, campo, valor)
    db.commit()
    db.refresh(deposito)
    return respuesta_ok(DepositoSalida.model_validate(deposito))


@router.patch("/{id_deposito}")
def modificar_deposito(id_deposito: int, datos: DepositoActualizar, db: Session = Depends(get_db)):
    deposito = buscar_deposito(db, id_deposito)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(deposito, campo, valor)
    db.commit()
    db.refresh(deposito)
    return respuesta_ok(DepositoSalida.model_validate(deposito))


@router.delete("/{id_deposito}")
def borrar_deposito(id_deposito: int, db: Session = Depends(get_db)):
    deposito = buscar_deposito(db, id_deposito)
    db.delete(deposito)
    db.commit()
    return respuesta_ok({"id_deposito": id_deposito, "borrado": True})
