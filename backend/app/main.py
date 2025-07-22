from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router
from app.core.logging import setup_logging
from app.services.time_sync_service import start_time_sync_service, stop_time_sync_service
from app.services.camera_health_service import start_camera_health_service, stop_camera_health_service

# Setup logging
setup_logging()
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting PFCAM application")
    await init_db()
    logger.info("Database initialized")
    
    # Start background services
    logger.info("Starting background services")
    await start_time_sync_service()
    logger.info("Time sync service started")
    await start_camera_health_service()
    logger.info("Camera health service started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PFCAM application")
    
    # Stop background services
    logger.info("Stopping background services")
    await stop_time_sync_service()
    logger.info("Time sync service stopped")
    await stop_camera_health_service()
    logger.info("Camera health service stopped")

# Determine if we should enable OpenAPI docs
enable_docs = os.getenv("ENVIRONMENT") != "production"

# Create FastAPI app
app = FastAPI(
    title="PFCAM - Industrial Event Camera Management",
    description="A comprehensive management application for industrial event cameras",
    version="1.0.0",
    docs_url="/api/docs" if enable_docs else None,
    redoc_url="/api/redoc" if enable_docs else None,
    openapi_url="/api/openapi.json" if enable_docs else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Use more restrictive origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Restrict methods
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Allow WebSocket connections in CSP
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' ws: wss:;"
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pfcam"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "PFCAM - Industrial Event Camera Management System",
        "version": "1.0.0",
        "docs": "/api/docs" if enable_docs else "Documentation disabled in production"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 