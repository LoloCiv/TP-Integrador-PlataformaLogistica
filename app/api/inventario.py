from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.respuestas import Paginacion, respuesta_ok, respuesta_paginada
from app.db import get_db
from app.models import Inventario, Producto
from app.schemas.inventario import InventarioActualizar, InventarioCrear, InventarioSalida

router = APIRouter(prefix="/inventario", tags=["Inventario"])


def buscar_inventario(db: Session, id_inventario: int) -> Inventario:
    inventario = db.get(Inventario, id_inventario)
    if inventario is None:
        raise HTTPException(status_code=404, detail=f"Inventario {id_inventario} no existe")
    return inventario


@router.get("")
def listar_inventario(pag: Paginacion = Depends(), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Inventario))
    inventarios = db.scalars(
        select(Inventario).order_by(Inventario.id_inventario).offset(pag.offset).limit(pag.limit)
    ).all()
    items = [InventarioSalida.model_validate(inventario) for inventario in inventarios]
    return respuesta_paginada(items, total, pag.limit, pag.offset)


@router.get("/{id_inventario}")
def ver_inventario(id_inventario: int, db: Session = Depends(get_db)):
    return respuesta_ok(InventarioSalida.model_validate(buscar_inventario(db, id_inventario)))


# Carga el stock inicial de un producto
@router.post("")
def crear_inventario(datos: InventarioCrear, db: Session = Depends(get_db)):
    if db.get(Producto, datos.id_producto) is None:
        raise HTTPException(status_code=404, detail=f"Producto {datos.id_producto} no existe")
    inventario = Inventario(**datos.model_dump())
    db.add(inventario)
    db.commit()
    db.refresh(inventario)
    return respuesta_ok(InventarioSalida.model_validate(inventario), status=201)


# Ajuste manual del stock
@router.patch("/{id_inventario}")
def modificar_stock(id_inventario: int, datos: InventarioActualizar, db: Session = Depends(get_db)):
    inventario = buscar_inventario(db, id_inventario)
    inventario.stock_actual = datos.stock_actual
    db.commit()
    db.refresh(inventario)
    return respuesta_ok(InventarioSalida.model_validate(inventario))


@router.delete("/{id_inventario}")
def borrar_inventario(id_inventario: int, db: Session = Depends(get_db)):
    inventario = buscar_inventario(db, id_inventario)
    db.delete(inventario)
    db.commit()
    return respuesta_ok({"id_inventario": id_inventario, "borrado": True})
