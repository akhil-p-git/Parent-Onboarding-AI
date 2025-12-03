"""
Zapier Triggers API - Main Application Entry Point.

A unified, real-time event ingestion system for the Zapier platform.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.core.openapi import (
    OPENAPI_TAGS,
    customize_openapi_schema,
    get_openapi_description,
)
from app.core.rate_limiter import RateLimitMiddleware
from app.core.redis import close_redis, init_redis
from app.core.tracing import instrument_sqlalchemy, setup_tracing

# Configure structured logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database connection established")

        # Instrument database for tracing
        from app.core.database import engine
        instrument_sqlalchemy(engine)
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    # Initialize Redis
    try:
        await init_redis()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}. Rate limiting may not work.")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")

    # Close database connections
    await close_db()
    logger.info("Database connections closed")

    # Close Redis connections
    await close_redis()
    logger.info("Redis connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    description=get_openapi_description(),
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else "/api/v1/openapi.json",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
    swagger_ui_parameters={
        "docExpansion": "none",
        "defaultModelsExpandDepth": -1,
        "syntaxHighlight.theme": "monokai",
        "tryItOutEnabled": True,
        "persistAuthorization": True,
        "filter": True,
    },
    redoc_url_config={
        "expandResponses": "200,201",
        "hideDownloadButton": False,
        "hideHostname": False,
    },
)


# Custom OpenAPI schema
def custom_openapi():
    """Generate customized OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )

    # Apply customizations
    openapi_schema = customize_openapi_schema(openapi_schema)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Setup OpenTelemetry tracing
setup_tracing(app)

# Register exception handlers
register_exception_handlers(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    exclude_paths=[
        "/",
        "/health",
        "/ready",
        "/live",
        "/metrics",
        "/api/v1/health",
        "/api/v1/health/ready",
        "/api/v1/health/live",
        "/api/v1/health/metrics",
        "/api/v1/health/metrics/prometheus",
        "/docs",
        "/redoc",
        "/openapi.json",
    ],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Root endpoint - redirect to docs or return basic info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None,
        "api": "/api/v1",
    }


@app.get("/health", tags=["System"], include_in_schema=False)
async def health_check_root() -> JSONResponse:
    """
    Health check endpoint (root-level shortcut).

    Simplified health check for load balancers and basic monitoring.
    For detailed health info, use /api/v1/health.
    """
    from app.core.database import engine
    from app.core.redis import get_redis

    status = "healthy"
    components = {}

    # Check database
    try:
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        components["database"] = "healthy"
    except Exception as e:
        components["database"] = "unhealthy"
        status = "degraded"

    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        components["redis"] = "healthy"
    except Exception:
        components["redis"] = "unhealthy"
        status = "degraded"

    status_code = 200 if status == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "version": settings.APP_VERSION,
            "components": components,
        },
    )


@app.get("/ready", tags=["System"], include_in_schema=False)
async def readiness_check_root() -> JSONResponse:
    """
    Readiness probe endpoint (root-level shortcut).

    Returns 200 if the service is ready to accept traffic.
    """
    from app.core.database import engine

    try:
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return JSONResponse(content={"ready": True})
    except Exception:
        return JSONResponse(status_code=503, content={"ready": False})


@app.get("/live", tags=["System"], include_in_schema=False)
async def liveness_check_root() -> JSONResponse:
    """
    Liveness probe endpoint (root-level shortcut).

    Returns 200 if the service process is alive.
    """
    return JSONResponse(content={"alive": True})


@app.get("/metrics", tags=["System"], include_in_schema=False)
async def metrics_redirect() -> JSONResponse:
    """Redirect to full metrics endpoint."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/api/v1/health/metrics/prometheus")


@app.get("/api/v1/openapi.json", include_in_schema=False)
async def get_openapi_spec():
    """
    Get the OpenAPI specification.

    Returns the complete OpenAPI 3.0 specification for the API.
    Useful for generating client SDKs and documentation.
    """
    return JSONResponse(content=app.openapi())


@app.get("/api/v1/openapi.yaml", include_in_schema=False)
async def get_openapi_spec_yaml():
    """
    Get the OpenAPI specification in YAML format.

    Returns the complete OpenAPI 3.0 specification in YAML format.
    """
    from fastapi.responses import Response

    try:
        import yaml

        yaml_content = yaml.dump(
            app.openapi(),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        return Response(
            content=yaml_content,
            media_type="application/x-yaml",
            headers={"Content-Disposition": "attachment; filename=openapi.yaml"},
        )
    except ImportError:
        return JSONResponse(
            status_code=501,
            content={"error": "YAML export not available. Install PyYAML."},
        )
