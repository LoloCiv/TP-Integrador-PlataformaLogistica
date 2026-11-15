from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

# Arma el JWT con el id del usuario (sub), su rol y el vencimiento, firmado con la clave secreta
def crear_token(id_usuario: int, rol: str, expira_minutos: int | None = None) -> str:
    if expira_minutos is None:
        expira_minutos = settings.jwt_expira_minutos

    payload = {
        "sub": str(id_usuario),
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expira_minutos),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algoritmo)


# Verifica la firma y el vencimiento; si algo falla lanza ValueError
def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algoritmo])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token vencido")
    except jwt.InvalidTokenError:
        raise ValueError("Token inválido")
