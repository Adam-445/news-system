from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging


from app.api.v1 import articles, users, auth, admin  # Import API routers
from app.db.database import engine, Base  # Database initialization
from app.core.logging import setup_logging  # Custom logging setup
from app.core.errors import APIError
from app.middleware.correlation import CorrelationMiddleware
from app.middleware.correlation import correlation_id

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


# Base.metadata.create_all(bind=engine)
# Create the FastAPI app
app = FastAPI(
    title="News Recommendation System",
    description="API for recommending news articles using machine learning",
    version="1.0.0",
)
app.add_middleware(CorrelationMiddleware())

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(articles.router, prefix="/api/v1/articles", tags=["Articles"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={
            "path": request.url.path,
            "method": request.method,
            "correlation_id": correlation_id.get(),
        },
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


@app.exception_handler(APIError)
async def handle_api_error(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "code": exc.status_code, "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        # error["loc"] is a tuple describing the location of the error,
        # we grab the last element which typically is the field name
        field = error["loc"][-1]
        errors.append({"field": field, "message": error["msg"], "type": error["type"]})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation failed", "code": 422, "detail": errors},
    )


# # Event handlers for startup and shutdown
# @app.lifespan("startup")
# async def on_startup():
#     # Initialize the database connection
#     print("Starting the application...")
#     # await init_db()


# @app.lifespan("shutdown")
# async def on_shutdown():
#     # Close database connections or other cleanup tasks
#     pass


# Health check endpoint
@app.get("/")
def health_check():
    return {"status": "ok", "message": "Welcome to the News Recommendation API!"}
