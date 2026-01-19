"""
FastAPI application entry point.

This module initializes the FastAPI application, configures middleware,
and sets up routes for the document conversion service.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.api.routes.convert import router as convert_router
from src.converters.pandoc import PandocConverter
from src.utils.file_handler import FileHandler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger(__name__)

# Track application start time
_start_time: float = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.
    
    Sets up resources on startup and cleans up on shutdown.
    """
    global _start_time
    _start_time = time.time()
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Temp directory: {settings.TEMP_DIR}")
    
    # Verify Pandoc installation
    try:
        converter = PandocConverter(
            pdf_engine=settings.PDF_ENGINE,
            timeout=settings.PANDOC_TIMEOUT,
        )
        pandoc_version = converter.get_pandoc_version()
        logger.info(f"Pandoc version: {pandoc_version}")
    except Exception as e:
        logger.error(f"Pandoc not available: {e}")
    
    # Ensure temp directory exists
    try:
        file_handler = FileHandler(temp_dir=settings.TEMP_DIR)
        logger.info(f"Temp directory ready: {file_handler.temp_dir}")
    except Exception as e:
        logger.error(f"Temp directory error: {e}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Duration: {duration:.3f}s"
    )
    
    return response


# Include routers
app.include_router(convert_router)


@app.get(
    "/health",
    summary="Health check endpoint",
    description="Returns the health status of the service, including Pandoc availability.",
    response_model=dict,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "pandoc_version": "3.1.3",
                        "uptime": 3600,
                        "checks": {
                            "pandoc": True,
                            "temp_dir": True,
                        },
                    }
                }
            },
        },
        503: {
            "description": "Service is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "version": "1.0.0",
                        "pandoc_version": "unknown",
                        "uptime": 0,
                        "checks": {
                            "pandoc": False,
                            "temp_dir": True,
                        },
                        "reason": "Pandoc is not available",
                    }
                }
            },
        },
    },
    tags=["health"],
)
async def health_check() -> dict[str, Any]:
    """Check the health status of the service.
    
    Returns:
        Health status information including:
        - status: 'healthy' or 'unhealthy'
        - version: Application version
        - pandoc_version: Installed Pandoc version
        - uptime: Seconds since application start
        - checks: Individual component status
    """
    global _start_time
    
    checks = {
        "pandoc": False,
        "temp_dir": False,
    }
    pandoc_version = "unknown"
    reasons = []
    
    # Check Pandoc availability
    try:
        converter = PandocConverter(
            pdf_engine=settings.PDF_ENGINE,
            timeout=settings.PANDOC_TIMEOUT,
        )
        pandoc_version = converter.get_pandoc_version()
        checks["pandoc"] = True
    except Exception as e:
        reasons.append(f"Pandoc is not available: {str(e)}")
    
    # Check temp directory
    try:
        file_handler = FileHandler(temp_dir=settings.TEMP_DIR)
        checks["temp_dir"] = file_handler.is_temp_dir_writable()
        if not checks["temp_dir"]:
            reasons.append("Temp directory is not writable")
    except Exception as e:
        reasons.append(f"Temp directory error: {str(e)}")
    
    # Determine overall status
    is_healthy = all(checks.values())
    uptime = int(time.time() - _start_time) if _start_time else 0
    
    response_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "version": settings.APP_VERSION,
        "pandoc_version": pandoc_version,
        "uptime": uptime,
        "checks": checks,
    }
    
    if not is_healthy:
        response_data["reason"] = "; ".join(reasons)
        return JSONResponse(status_code=503, content=response_data)
    
    return response_data


@app.get(
    "/",
    summary="Root endpoint",
    description="Returns basic service information.",
    tags=["info"],
)
async def root() -> dict[str, str]:
    """Root endpoint with basic service info.
    
    Returns:
        Basic service information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs": "/docs",
        "health": "/health",
    }
