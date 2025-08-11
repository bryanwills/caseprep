"""
FastAPI application factory and configuration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.database import engine, sessionmanager
from app.core.exceptions import CasePrepException
from app.core.logging import configure_logging


# Configure structured logging
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler for startup and shutdown events.
    """
    # Startup
    logger.info("Starting CasePrep API...")
    
    # Initialize database
    sessionmanager.init(get_settings().DATABASE_URL)
    
    yield
    
    # Shutdown
    logger.info("Shutting down CasePrep API...")
    if sessionmanager._engine is not None:
        await sessionmanager.close()


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    settings = get_settings()
    
    # Configure logging
    configure_logging(settings.LOG_LEVEL, settings.ENVIRONMENT)
    
    # Configure Sentry if DSN is provided
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(auto_enabling_integrations=False),
                SqlalchemyIntegration(),
            ],
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
        )
    
    # Create FastAPI application
    app = FastAPI(
        title="CasePrep API",
        description="Privacy-first legal transcription platform API",
        version="0.1.0",
        openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
        docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
        # Security headers
        swagger_ui_parameters={
            "displayRequestDuration": True,
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
        }
    )
    
    # Security Middleware
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=settings.ALLOWED_HOSTS
        )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Request-ID",
            "X-Correlation-ID",
        ],
        expose_headers=["X-Request-ID", "X-Correlation-ID"],
    )
    
    # Request ID Middleware
    @app.middleware("http")
    async def add_request_id_header(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or f"req_{id(request)}"
        
        # Add to context for logging
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        # Clear context after request
        structlog.contextvars.clear_contextvars()
        
        return response
    
    # Global Exception Handler
    @app.exception_handler(CasePrepException)
    async def caseprep_exception_handler(request: Request, exc: CasePrepException):
        """Handle custom CasePrep exceptions."""
        logger.error(
            "CasePrep exception occurred",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path,
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(
            "Unexpected exception occurred",
            exception=str(exc),
            exception_type=type(exc).__name__,
            path=request.url.path,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                }
            },
        )
    
    # Health Check Endpoint
    @app.get("/health", tags=["System"])
    async def health_check():
        """Health check endpoint for load balancers and monitoring."""
        return {
            "status": "healthy",
            "version": "0.1.0",
            "environment": settings.ENVIRONMENT,
        }
    
    @app.get("/health/ready", tags=["System"])
    async def readiness_check():
        """Readiness check for Kubernetes deployments."""
        try:
            # Check database connectivity
            async with sessionmanager.session() as session:
                await session.execute("SELECT 1")
            
            return {
                "status": "ready",
                "checks": {
                    "database": "healthy",
                }
            }
        except Exception as e:
            logger.error("Readiness check failed", error=str(e))
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "checks": {
                        "database": "unhealthy",
                    }
                }
            )
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    return app


# Create the application instance
app = create_application()