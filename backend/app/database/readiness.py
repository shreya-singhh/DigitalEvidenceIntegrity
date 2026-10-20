from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.diagnostics import safe_exception_diagnostics
from app.core.config import settings
from app.database.session import engine
from app.models.user import User


def database_readiness_response() -> JSONResponse:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            table_names = set(inspect(connection).get_table_names())
            if "users" not in table_names:
                missing_columns = sorted(User.__table__.columns.keys())
            else:
                available = {
                    column["name"] for column in inspect(connection).get_columns("users")
                }
                missing_columns = sorted(set(User.__table__.columns.keys()) - available)
    except SQLAlchemyError as exc:
        logger.error(
            "Database readiness check failed; diagnostics={diagnostics}",
            diagnostics=safe_exception_diagnostics(exc),
        )
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "detail": "Database is unavailable."},
        )

    if missing_columns:
        logger.error(
            "Database readiness check found missing user columns: {columns}",
            columns=missing_columns,
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "detail": "Database schema migration is required.",
            },
        )

    return JSONResponse(
        status_code=200,
        content={"status": "ready", "version": settings.app_version},
    )
