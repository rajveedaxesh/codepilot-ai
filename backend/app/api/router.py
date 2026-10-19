from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.projects import router as projects_router
from backend.app.api.sessions import router as sessions_router
from backend.app.api.benchmarks import router as benchmarks_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(projects_router)
api_router.include_router(sessions_router)
api_router.include_router(benchmarks_router)
