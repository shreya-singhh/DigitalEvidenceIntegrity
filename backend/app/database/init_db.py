from typing import Any

from sqlalchemy.exc import OperationalError

from .session import engine
from .base import Base
from ..core.diagnostics import safe_exception_diagnostics
from ..core.logging import logger


def init_db() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except OperationalError as error:
        logger.error(
            "Database initialization failed; diagnostics={diagnostics}",
            diagnostics=safe_exception_diagnostics(error),
        )
        raise
