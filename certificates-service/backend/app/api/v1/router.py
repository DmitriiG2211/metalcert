from fastapi import APIRouter

from app.api.v1.endpoints import auth, certificates, search, dashboard, export

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
