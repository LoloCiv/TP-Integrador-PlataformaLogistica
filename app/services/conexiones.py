import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


# Lleva la cuenta de quién está mirando cada orden por WebSocket
class GestorConexiones:

    def __init__(self):
        # id_orden → conjunto de WebSockets conectados a esa orden
        self.canales: dict[int, set[WebSocket]] = defaultdict(set)

    # Acepta la conexión y la suma al canal de su orden
    async def conectar(self, id_orden: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.canales[id_orden].add(websocket)
        logger.info("WebSocket conectado a la orden %s (%s mirando)", id_orden, len(self.canales[id_orden]))

    # La saca; si el canal queda vacío, lo borra
    def desconectar(self, id_orden: int, websocket: WebSocket) -> None:
        self.canales[id_orden].discard(websocket)
        if not self.canales[id_orden]:
            del self.canales[id_orden]

    # Manda los datos a todos los que miran esa orden; si una conexión falla, la descarta
    async def enviar(self, id_orden: int, datos: dict) -> None:
        for websocket in list(self.canales.get(id_orden, ())):
            try:
                await websocket.send_json(datos)
            except Exception:
                self.desconectar(id_orden, websocket)
