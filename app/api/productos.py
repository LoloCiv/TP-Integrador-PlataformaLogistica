from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.respuestas import Paginacion, respuesta_ok, respuesta_paginada
from app.db import get_db
from app.models import Deposito, Producto
from app.schemas.producto import ProductoActualizar, ProductoCrear, ProductoSalida

router = APIRouter(prefix="/productos", tags=["Productos"])


def buscar_producto(db: Session, id_producto: int) -> Producto:
    producto = db.get(Producto, id_producto)
    if producto is None:
        raise HTTPException(status_code=404, detail=f"Producto {id_producto} no existe")
    return producto


# Para no crear productos en un depósito que no existe
def verificar_deposito(db: Session, id_deposito: int) -> None:
    if db.get(Deposito, id_deposito) is None:
        raise HTTPException(status_code=404, detail=f"Depósito {id_deposito} no existe")


# Lo usan PUT y PATCH. El precio pasa por actualizar_precio para validarlo
def aplicar_cambios(producto: Producto, cambios: dict, db: Session) -> None:
    if "id_deposito" in cambios:
        verificar_deposito(db, cambios["id_deposito"])
    if "precio" in cambios:
        producto.actualizar_precio(cambios.pop("precio"))
    for campo, valor in cambios.items():
        setattr(producto, campo, valor)


@router.get("")
def listar_productos(pag: Paginacion = Depends(), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Producto))
    productos = db.scalars(
        select(Producto).order_by(Producto.id_producto).offset(pag.offset).limit(pag.limit)
    ).all()
    items = [ProductoSalida.model_validate(producto) for producto in productos]
    return respuesta_paginada(items, total, pag.limit, pag.offset)


@router.get("/{id_producto}")
def ver_producto(id_producto: int, db: Session = Depends(get_db)):
    return respuesta_ok(ProductoSalida.model_validate(buscar_producto(db, id_producto)))


@router.post("")
def crear_producto(datos: ProductoCrear, db: Session = Depends(get_db)):
    verificar_deposito(db, datos.id_deposito)
    producto = Producto(**datos.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return respuesta_ok(ProductoSalida.model_validate(producto), status=201)


@router.put("/{id_producto}")
def reemplazar_producto(id_producto: int, datos: ProductoCrear, db: Session = Depends(get_db)):
    producto = buscar_producto(db, id_producto)
    aplicar_cambios(producto, datos.model_dump(), db)
    db.commit()
    db.refresh(producto)
    return respuesta_ok(ProductoSalida.model_validate(producto))


@router.patch("/{id_producto}")
def modificar_producto(id_producto: int, datos: ProductoActualizar, db: Session = Depends(get_db)):
    producto = buscar_producto(db, id_producto)
    aplicar_cambios(producto, datos.model_dump(exclude_unset=True), db)
    db.commit()
    db.refresh(producto)
    return respuesta_ok(ProductoSalida.model_validate(producto))


@router.delete("/{id_producto}")
def borrar_producto(id_producto: int, db: Session = Depends(get_db)):
    producto = buscar_producto(db, id_producto)
    db.delete(producto)
    db.commit()
    return respuesta_ok({"id_producto": id_producto, "borrado": True})
