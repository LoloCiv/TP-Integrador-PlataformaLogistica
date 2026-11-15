import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errores import NoEncontrado
from app.models import Cliente, DetalleOrden, Orden, Producto, Repartidor, Ruta, Vehiculo
from app.models.enums import EstadoOrden, EstadoRepartidor, EstadoVehiculo
from app.schemas.orden import OrdenCrear
from app.services.cola_mensajes import ColaMensajes, Coordenada, MensajeRuta

logger = logging.getLogger(__name__)

# Cambios de estado permitidos por /estado. Los demás tienen su propio método
TRANSICIONES = {
    EstadoOrden.EN_CAMINO: [EstadoOrden.ENTREGADA],
}


# Toda la lógica de las órdenes. Recibe la base y la cola por constructor (inyección de dependencias)
class GestorPedidos:

    def __init__(self, db: Session, cola: ColaMensajes):
        self.db = db
        self.cola = cola

    # Busca la orden o lanza NoEncontrado (404)
    def get_orden_by_id(self, id_orden: int) -> Orden:
        orden = self.db.get(Orden, id_orden)
        if orden is None:
            raise NoEncontrado(f"Orden {id_orden} no existe")
        return orden

    # Valida productos, depósito y stock; después arma la orden, descuenta stock y guarda
    def crear_orden(self, cliente: Cliente, datos: OrdenCrear) -> Orden:
        list_productos = []
        for detalle in datos.detalles:
            producto = self.db.get(Producto, detalle.id_producto)
            if producto is None:
                raise NoEncontrado(f"Producto {detalle.id_producto} no existe")
            list_productos.append((producto, detalle.cantidad))

        #Se verifica que todos los productos sean del mismo depósito y que tengan stock suficiente
        # Todos los productos tienen que salir del mismo depósito
        deposito_ids = {producto.id_deposito for producto, cantidad in list_productos}
        if len(deposito_ids) > 1:
            raise ValueError("Todos los productos deben ser del mismo depósito")

        # Que cada producto tenga inventario y stock suficiente
        for producto, cantidad in list_productos:
            if producto.inventario is None:
                raise ValueError(f"Producto {producto.id_producto} no tiene inventario cargado")
            if not producto.inventario.hay_stock_suficiente(cantidad):
                raise ValueError(f"Producto {producto.id_producto} no tiene stock suficiente")

        # El cliente viene del token y el estado arranca en PENDIENTE
        orden = Orden(
            cliente=cliente,
            direccion_entrega=datos.direccion_entrega,
            latitud=datos.latitud,
            longitud=datos.longitud,
            estado_orden=EstadoOrden.PENDIENTE,
        )

        # Se descuentan los stocks y se crean los detalles de la orden
        # Descuenta stock y guarda el precio del momento en cada detalle
        for producto, cantidad in list_productos:
            producto.inventario.descontar_stock(cantidad)
            detalle_orden = DetalleOrden(producto=producto, cantidad=cantidad, precio_unitario=producto.precio)
            orden.agregar_detalle(detalle_orden)

        self.db.add(orden)
        self.db.commit()
        self.db.refresh(orden)
        logger.info("Orden %s creada (cliente=%s, total=%s)", orden.id_orden, cliente.id_cliente, orden.total)
        return orden

    # Cambia el estado solo si la transición está permitida; al entregar guarda la fecha
    def actualizar_estado(self, id_orden: int, nuevo_estado: EstadoOrden, id_repartidor: int | None = None) -> Orden:
        orden = self.get_orden_by_id(id_orden)

        # Si viene un repartidor, la orden tiene que estar en una ruta suya
        if id_repartidor is not None and (orden.ruta is None or orden.ruta.id_repartidor != id_repartidor):
            raise ValueError(f"La orden {id_orden} no es del repartidor {id_repartidor}")

        if nuevo_estado not in TRANSICIONES.get(orden.estado_orden, []):
            raise ValueError(f"No se puede pasar de {orden.estado_orden} a {nuevo_estado}")
        orden.estado_orden = nuevo_estado
        if nuevo_estado == EstadoOrden.ENTREGADA:
            orden.fecha_entrega = datetime.now(timezone.utc)
            ruta = orden.ruta
            if all(orden_de_ruta.estado_orden != EstadoOrden.EN_CAMINO for orden_de_ruta in ruta.ordenes):
                ruta.repartidor.cambiar_estado(EstadoRepartidor.DISPONIBLE)
                ruta.vehiculo.cambiar_estado(EstadoVehiculo.DISPONIBLE)
        self.db.commit()
        self.db.refresh(orden)
        logger.info("Orden %s actualizada a estado %s", orden.id_orden, orden.estado_orden)
        return orden

    # Solo antes de salir (PENDIENTE o CONFIRMADA). Devuelve el stock
    def cancelar_orden(self, id_orden: int) -> Orden:
        orden = self.get_orden_by_id(id_orden)

        if orden.estado_orden in [EstadoOrden.EN_CAMINO, EstadoOrden.ENTREGADA, EstadoOrden.CANCELADA]:
            raise ValueError(f"No se puede cancelar una orden {orden.estado_orden}")

        for detalle in orden.detalles:
            detalle.producto.inventario.stock_actual += detalle.cantidad

        ruta = orden.ruta
        orden.estado_orden = EstadoOrden.CANCELADA
        self.db.commit()
        self.db.refresh(orden)

        if ruta is not None and any(otra.estado_orden == EstadoOrden.CONFIRMADA for otra in ruta.ordenes):
            self.cola.publicar(self._armar_mensaje(ruta))
        logger.info("Orden %s cancelada", orden.id_orden)
        return orden


    # Mensaje para el microservicio: el depósito primero y después cada entrega
    def _armar_mensaje(self, ruta: Ruta) -> MensajeRuta:

        list_ordenes = [orden for orden in ruta.ordenes if orden.estado_orden == EstadoOrden.CONFIRMADA]
        mensaje = MensajeRuta(orden_ids=[orden.id_orden for orden in list_ordenes], paradas=[])

        deposito = list_ordenes[0].detalles[0].producto.deposito

        mensaje.paradas.append(Coordenada(float(deposito.latitud), float(deposito.longitud)))
        for orden in list_ordenes:
            mensaje.paradas.append(Coordenada(float(orden.latitud), float(orden.longitud)))
        return mensaje

    # Reusa la ruta del repartidor + vehículo si todavía tiene órdenes CONFIRMADA; si no, crea una
    def _ruta_abierta(self, repartidor: Repartidor, vehiculo: Vehiculo) -> Ruta:

        ruta = self.db.scalar(
            select(Ruta)
            .join(Ruta.ordenes)
            .where(
                Ruta.id_repartidor == repartidor.id_repartidor,
                Ruta.id_vehiculo == vehiculo.id_vehiculo,
                Orden.estado_orden == EstadoOrden.CONFIRMADA,
            )
            .limit(1)
        )
        if ruta is None:
            ruta = Ruta(repartidor=repartidor, vehiculo=vehiculo)
            self.db.add(ruta)
        return ruta

    # Valida repartidor, vehículo y capacidad, mete la orden en una ruta y avisa al microservicio
    def asignar_repartidor(self, id_orden: int, id_repartidor: int, id_vehiculo: int) -> Orden:

        orden = self.get_orden_by_id(id_orden)
        if orden.estado_orden != EstadoOrden.PENDIENTE:
            raise ValueError(f"Orden {id_orden} no está PENDIENTE, sino {orden.estado_orden}")
        repartidor = self.db.get(Repartidor, id_repartidor)
        if repartidor is None:
            raise NoEncontrado(f"Repartidor {id_repartidor} no existe")
        if not repartidor.esta_disponible():
            raise ValueError(f"Repartidor {id_repartidor} no está disponible")
        vehiculo = self.db.get(Vehiculo, id_vehiculo)
        if vehiculo is None:
            raise NoEncontrado(f"Vehículo {id_vehiculo} no existe")

        if vehiculo.id_repartidor != id_repartidor:
            raise ValueError(f"Vehículo {id_vehiculo} no pertenece al repartidor {id_repartidor}")
        if not vehiculo.esta_disponible():
            raise ValueError(f"Vehículo {id_vehiculo} no está disponible")

        cargadas = self.db.scalars(
            select(Orden)
            .join(Orden.ruta)
            .where(
                Ruta.id_repartidor == id_repartidor,
                Ruta.id_vehiculo == id_vehiculo,
                Orden.estado_orden == EstadoOrden.CONFIRMADA,
            )
        ).all()
        carga = sum((cargada.calcular_peso() for cargada in cargadas), Decimal("0")) + orden.calcular_peso()
        if carga > vehiculo.capacidad_kg:
            raise ValueError(f"La carga de la ruta ({carga} kg) supera la capacidad del vehículo ({vehiculo.capacidad_kg} kg)")

        ruta = self._ruta_abierta(repartidor, vehiculo)
        orden.ruta = ruta
        orden.estado_orden = EstadoOrden.CONFIRMADA
        self.db.commit()
        self.db.refresh(orden)

        # Se publica después del commit, así el microservicio encuentra los datos guardados
        self.cola.publicar(self._armar_mensaje(ruta))
        logger.info("Orden %s asignada al repartidor %s (ruta %s)", orden.id_orden, id_repartidor, ruta.id_ruta)
        return orden

    # El repartidor sale: todas las órdenes CONFIRMADA de su ruta pasan juntas a EN_CAMINO
    def iniciar_ruta(self, id_ruta: int, id_repartidor: int) -> list[Orden]:

        ruta = self.db.get(Ruta, id_ruta)
        if ruta is None:
            raise NoEncontrado(f"Ruta {id_ruta} no existe")
        if ruta.id_repartidor != id_repartidor:
            raise ValueError(f"La ruta {id_ruta} no es del repartidor {id_repartidor}")
        ordenes = [orden for orden in ruta.ordenes if orden.estado_orden == EstadoOrden.CONFIRMADA]
        if not ordenes:
            raise ValueError(f"La ruta {id_ruta} no tiene órdenes CONFIRMADA para iniciar")
        if not ruta.repartidor.esta_disponible():
            raise ValueError(f"Repartidor {id_repartidor} no está disponible")
        if not ruta.vehiculo.esta_disponible():
            raise ValueError(f"Vehículo {ruta.id_vehiculo} no está disponible")

        for orden in ordenes:
            orden.estado_orden = EstadoOrden.EN_CAMINO
        ruta.repartidor.cambiar_estado(EstadoRepartidor.EN_RUTA)
        ruta.vehiculo.cambiar_estado(EstadoVehiculo.EN_USO)
        self.db.commit()
        logger.info("Ruta %s iniciada: órdenes %s EN_CAMINO", id_ruta, [orden.id_orden for orden in ordenes])
        return ordenes
