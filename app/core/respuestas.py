from fastapi import Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


# Formato estándar de éxito: {status, data}
def respuesta_ok(data, status: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=jsonable_encoder({"status": status, "data": data}),
    )


# Lo mismo para listados, con los datos de paginación
def respuesta_paginada(items: list, total: int, limit: int, offset: int) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(
            {
                "status": 200,
                "data": items,
                "paginacion": {"total": total, "limit": limit, "offset": offset},
            }
        ),
    )


# Formato estándar de error: {status, error}
def respuesta_error(status: int, mensaje: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"status": status, "error": mensaje},
    )


# Lee ?limit= y ?offset= de la URL (se usa con Depends())
class Paginacion:
    def __init__(
        self,
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ):
        self.limit = limit
        self.offset = offset
