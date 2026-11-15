import logging
from pathlib import Path

from app.core.config import settings


# Logs a la consola y a logs/app.log, con fecha, nivel y módulo
def configurar_logging(nivel: str | None = None, archivo: str = "logs/app.log") -> None:
    Path(archivo).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=(nivel or settings.log_level).upper(),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(archivo, encoding="utf-8"),
        ],
        force=True,
    )
