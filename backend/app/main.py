import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.db.session import init_db
from backend.app.api.router import api_router
from backend.app.services.sanitizer import SecurityError
from backend.app.services.inspector import SafeExtractionError
from backend.app.services.patch_engine import PatchError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("codepilot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite database schema
    logger.info("Initializing CodePilot AI database and storage directories...")
    init_db()
    logger.info(f"CodePilot AI started successfully. Storage path: {settings.DATA_DIR}")
    yield
    # Shutdown
    logger.info("CodePilot AI shutting down.")

app = FastAPI(
    title="CodePilot AI API",
    description="Autonomous AI Software Engineering Agent — Inspection, Bug Diagnosis, Patch Generation, and Verification",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(SecurityError)
async def security_error_handler(request: Request, exc: SecurityError):
    logger.warning(f"Security boundary alert: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": f"Security boundary violation: {str(exc)}"}
    )

@app.exception_handler(SafeExtractionError)
async def archive_error_handler(request: Request, exc: SafeExtractionError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": f"Archive validation error: {str(exc)}"}
    )

@app.exception_handler(PatchError)
async def patch_error_handler(request: Request, exc: PatchError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": f"Patch error: {str(exc)}"}
    )

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

frontend_dist = settings.BASE_DIR.parent / "frontend" / "dist"
if (frontend_dist / "index.html").exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        file_candidate = frontend_dist / full_path
        if full_path and file_candidate.is_file():
            return FileResponse(file_candidate)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "app": settings.APP_NAME,
            "version": "1.0.0",
            "docs": "/docs",
            "health": f"{settings.API_V1_PREFIX}/health"
        }

