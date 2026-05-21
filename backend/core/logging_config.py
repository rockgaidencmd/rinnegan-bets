"""Centralized logging configuration.

Goal: cuando algo falla en runtime, queremos ver QUÉ pasó y DÓNDE
sin perdernos en el ruido de uvicorn/sqlalchemy/httpx.

Tres niveles de control:
  - Root logger: WARNING por defecto (silencia libs ruidosas)
  - Namespaces de la app (api.*, core.*, data.*, db.*, scripts.*):
    nivel configurable vía LOG_LEVEL env var (default INFO)
  - Loggers de libs específicas (httpx, sqlalchemy.engine): WARNING
    en runtime normal, pero respetan LOG_LEVEL si está en DEBUG

Uso:
    from core.logging_config import setup_logging
    setup_logging()                   # lee LOG_LEVEL o usa INFO
    setup_logging(level="DEBUG")      # explícito
"""

from __future__ import annotations

import logging
import os
import sys


APP_NAMESPACES = ("api", "core", "data", "db", "scripts")

# Libs que pueden hacer mucho ruido — las contenemos a WARNING aunque
# el resto del app esté en DEBUG, salvo que el usuario lo pida explícito.
NOISY_LIBS = ("httpx", "httpcore", "urllib3", "sqlalchemy.engine")


def setup_logging(level: str | None = None, *, verbose_libs: bool = False) -> None:
    """Configura el logging global del backend.

    Args:
        level: Nivel para los namespaces de la app (api.*, core.*, etc).
               Si es None, lee la env var LOG_LEVEL. Default final: "INFO".
        verbose_libs: Si True, también activa DEBUG en httpx/sqlalchemy
                      (útil para depurar requests HTTP o SQL crudo).
    """
    resolved = (level or os.environ.get("LOG_LEVEL") or "INFO").upper()
    if resolved not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(f"invalid log level: {resolved}")

    fmt = "%(asctime)s | %(levelname)-7s | %(name)-30s | %(message)s"
    datefmt = "%H:%M:%S"

    # Si ya hay handlers configurados (ej. tests, uvicorn las pone),
    # los reemplazamos para que nuestro formato gane.
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    root.addHandler(handler)
    root.setLevel(logging.WARNING)

    for namespace in APP_NAMESPACES:
        logging.getLogger(namespace).setLevel(resolved)

    libs_level = resolved if verbose_libs else "WARNING"
    for lib in NOISY_LIBS:
        logging.getLogger(lib).setLevel(libs_level)
