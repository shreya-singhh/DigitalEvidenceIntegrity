from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.router import api_router
from app.core.config import settings
from app.core.diagnostics import safe_exception_diagnostics
from app.core.logging import configure_logging
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.database.init_db import init_db

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Digital Evidence Integrity backend API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.include_router(api_router)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting Digital Evidence Integrity backend")
    init_db()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("Shutting down Digital Evidence Integrity backend")


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "version": settings.app_version},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"loc": error.get("loc", ()), "msg": error.get("msg", "Invalid value"), "type": error.get("type", "value_error")}
        for error in exc.errors()
    ]
    logger.warning("Request validation failed: {errors}", errors=errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    route = request.scope.get("route")
    route_path = getattr(route, "path", request.url.path)
    logger.error(
        "Unhandled request exception; method={method} route={route} diagnostics={diagnostics}",
        method=request.method,
        route=route_path,
        diagnostics=safe_exception_diagnostics(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
