from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1 import articles, users, auth  # Import API routers
# from app.core.logging import setup_logging  # Custom logging setup
# from app.db.database import init_db  # Database initialization
from app.db.database import engine, Base  # Database initialization
# from app.core.config import settings  # App settings (e.g., from `config.py`)

# Initialize logging
# setup_logging()

# Base.metadata.create_all(bind=engine)
# Create the FastAPI app
app = FastAPI(
    title="News Recommendation System",
    description="API for recommending news articles using machine learning",
    version="1.0.0",
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(articles.router, prefix="/api/v1/articles", tags=["Articles"])


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
