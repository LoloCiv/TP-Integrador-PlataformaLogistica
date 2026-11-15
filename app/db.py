from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Conexión a Postgres, armada con los datos del .env
engine = create_engine(settings.database_url)
# Fábrica de sesiones: cada pedido usa la suya
SessionLocal = sessionmaker(bind=engine, autoflush=False)


# Clase madre de todos los modelos del ORM
class Base(DeclarativeBase):
    pass


# Dependencia: abre una sesión por pedido y la cierra al terminar, pase lo que pase
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Crea las tablas que falten (se llama al arrancar). El import registra los modelos en Base
def crear_tablas():
    import app.models

    Base.metadata.create_all(bind=engine)
