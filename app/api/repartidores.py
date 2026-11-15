from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.respuestas import Paginacion, respuesta_ok, respuesta_paginada
from app.db import get_db
from app.models import Repartidor
from app.schemas.repartidor import RepartidorActualizar, RepartidorCrear, RepartidorSalida

router = APIRouter(prefix="/repartidores", tags=["Repartidores"])


# Busca el repartidor o corta con 404
def buscar_repartidor(db: Session, id_repartidor: int) -> Repartidor:
    repartidor = db.get(Repartidor, id_repartidor)
    if repartidor is None:
        raise HTTPException(status_code=404, detail=f"Repartidor {id_repartidor} no existe")
    return repartidor


@router.get("")
def listar_repartidores(pag: Paginacion = Depends(), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Repartidor))
    repartidores = db.scalars(
        select(Repartidor).order_by(Repartidor.id_repartidor).offset(pag.offset).limit(pag.limit)
    ).all()
    items = [RepartidorSalida.model_validate(repartidor) for repartidor in repartidores]
    return respuesta_paginada(items, total, pag.limit, pag.offset)


@router.get("/{id_repartidor}")
def ver_repartidor(id_repartidor: int, db: Session = Depends(get_db)):
    return respuesta_ok(RepartidorSalida.model_validate(buscar_repartidor(db, id_repartidor)))


# Igual que los clientes: la contraseña va hasheada
@router.post("")
def crear_repartidor(datos: RepartidorCrear, db: Session = Depends(get_db)):
    repartidor = Repartidor(**datos.model_dump(exclude={"password"}))
    repartidor.cambiar_password(datos.password)
    db.add(repartidor)
    db.commit()
    db.refresh(repartidor)
    return respuesta_ok(RepartidorSalida.model_validate(repartidor), status=201)


# El estado pasa por cambiar_estado para validarlo
@router.patch("/{id_repartidor}")
def modificar_repartidor(id_repartidor: int, datos: RepartidorActualizar, db: Session = Depends(get_db)):
    repartidor = buscar_repartidor(db, id_repartidor)
    cambios = datos.model_dump(exclude_unset=True)
    if "estado_repartidor" in cambios:
        repartidor.cambiar_estado(cambios.pop("estado_repartidor"))
    for campo, valor in cambios.items():
        setattr(repartidor, campo, valor)
    db.commit()
    db.refresh(repartidor)
    return respuesta_ok(RepartidorSalida.model_validate(repartidor))


@router.delete("/{id_repartidor}")
def borrar_repartidor(id_repartidor: int, db: Session = Depends(get_db)):
    repartidor = buscar_repartidor(db, id_repartidor)
    db.delete(repartidor)
    db.commit()
    return respuesta_ok({"id_repartidor": id_repartidor, "borrado": True})
