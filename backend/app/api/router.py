from fastapi import APIRouter

from .routes.audit import router as audit_router
from .routes.auth import router as auth_router
from .routes.cases import router as cases_router
from .routes.chain_of_custody import router as chain_of_custody_router
from .routes.evidence import router as evidence_router
from .routes.health import router as health_router
from .routes.metadata import router as metadata_router
from .routes.dashboard import router as dashboard_router
from .routes.reports import router as reports_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(cases_router)
api_router.include_router(evidence_router)
api_router.include_router(chain_of_custody_router)
api_router.include_router(metadata_router)
api_router.include_router(audit_router)
api_router.include_router(reports_router)
