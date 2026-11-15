from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.respuestas import Paginacion, respuesta_ok, respuesta_paginada
from app.db import get_db
from app.models import Repartidor, Vehiculo
from app.schemas.vehiculo import VehiculoActualizar, VehiculoCrear, VehiculoSalida

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])


def buscar_vehiculo(db: Session, id_vehiculo: int) -> Vehiculo:
    vehiculo = db.get(Vehiculo, id_vehiculo)
    if vehiculo is None:
        raise HTTPException(status_code=404, detail=f"Vehículo {id_vehiculo} no existe")
    return vehiculo


# El repartidor es opcional, pero si viene tiene que existir
def verificar_repartidor(db: Session, id_repartidor: int | None) -> None:
    if id_repartidor is not None and db.get(Repartidor, id_repartidor) is None:
        raise HTTPException(status_code=404, detail=f"Repartidor {id_repartidor} no existe")


# Lo usan PUT y PATCH. El estado pasa por cambiar_estado para validarlo
def aplicar_cambios(vehiculo: Vehiculo, cambios: dict, db: Session) -> None:
    if "id_repartidor" in cambios:
        verificar_repartidor(db, cambios["id_repartidor"])
    if "estado_vehiculo" in cambios:
        vehiculo.cambiar_estado(cambios.pop("estado_vehiculo"))
    for campo, valor in cambios.items():
        setattr(vehiculo, campo, valor)


@router.get("")
def listar_vehiculos(pag: Paginacion = Depends(), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Vehiculo))
    vehiculos = db.scalars(
        select(Vehiculo).order_by(Vehiculo.id_vehiculo).offset(pag.offset).limit(pag.limit)
    ).all()
    items = [VehiculoSalida.model_validate(vehiculo) for vehiculo in vehiculos]
    return respuesta_paginada(items, total, pag.limit, pag.offset)


@router.get("/{id_vehiculo}")
def ver_vehiculo(id_vehiculo: int, db: Session = Depends(get_db)):
    return respuesta_ok(VehiculoSalida.model_validate(buscar_vehiculo(db, id_vehiculo)))


@router.post("")
def crear_vehiculo(datos: VehiculoCrear, db: Session = Depends(get_db)):
    verificar_repartidor(db, datos.id_repartidor)
    vehiculo = Vehiculo(**datos.model_dump())
    db.add(vehiculo)
    db.commit()
    db.refresh(vehiculo)
    return respuesta_ok(VehiculoSalida.model_validate(vehiculo), status=201)


@router.put("/{id_vehiculo}")
def reemplazar_vehiculo(id_vehiculo: int, datos: VehiculoCrear, db: Session = Depends(get_db)):
    vehiculo = buscar_vehiculo(db, id_vehiculo)
    aplicar_cambios(vehiculo, datos.model_dump(), db)
    db.commit()
    db.refresh(vehiculo)
    return respuesta_ok(VehiculoSalida.model_validate(vehiculo))


@router.patch("/{id_vehiculo}")
def modificar_vehiculo(id_vehiculo: int, datos: VehiculoActualizar, db: Session = Depends(get_db)):
    vehiculo = buscar_vehiculo(db, id_vehiculo)
    aplicar_cambios(vehiculo, datos.model_dump(exclude_unset=True), db)
    db.commit()
    db.refresh(vehiculo)
    return respuesta_ok(VehiculoSalida.model_validate(vehiculo))


@router.delete("/{id_vehiculo}")
def borrar_vehiculo(id_vehiculo: int, db: Session = Depends(get_db)):
    vehiculo = buscar_vehiculo(db, id_vehiculo)
    db.delete(vehiculo)
    db.commit()
    return respuesta_ok({"id_vehiculo": id_vehiculo, "borrado": True})
