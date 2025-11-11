from fastapi import FastAPI

from backend.app.common.config.settings import settings
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.lifespan import lifespan
from backend.app.core.middleware import register_middleware
from backend.app.core.routes import include_api_routes


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.

    Keeps the global import surface minimal and makes testing / composition easier.
    """
    app = FastAPI(
        title="News Recommendation System",
        description="API for recommending news articles using machine learning",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    register_middleware(app)
    include_api_routes(app)
    register_exception_handlers(app)

    @app.get(
        "/health",
        summary="API Health Check",
        response_description="System status information",
        tags=["System"],
    )
    async def health_check() -> dict:  # noqa: D401 - simple status endpoint
        return {
            "status": "ok",
            "version": app.version,
            "environment": settings.environment,
        }

    return app
