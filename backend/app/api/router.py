from fastapi import APIRouter

from app.api.routes.analyze import router as analyze_router
from app.api.routes.report import router as report_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.suggest import router as suggest_router
from app.api.routes.upload import router as upload_router

api_router = APIRouter()
api_router.include_router(upload_router)
api_router.include_router(analyze_router)
api_router.include_router(suggest_router)
api_router.include_router(report_router)
api_router.include_router(sessions_router)
