from typing import Any, Dict, Sequence

from fastapi import FastAPI

from backend.app.modules.admin.routes import admin_routes
from backend.app.modules.articles.routes import article_routes
from backend.app.modules.auth.routes import auth_routes
from backend.app.modules.users.routes import preference_routes, user_routes


def include_api_routes(app: FastAPI) -> None:
    """Attach versioned API routers with consistent tags & common responses."""
    api_routers: Sequence[tuple] = (
        (auth_routes.router, "/auth", ["Authentication"]),
        (user_routes.router, "/users", ["Users"]),
        (preference_routes.router, "/preferences", ["Preferences"]),
        (article_routes.router, "/articles", ["Articles"]),
        (admin_routes.router, "/admin", ["Admin Management"]),
    )

    common_responses: Dict[int | str, Dict[str, Any]] = {
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not Found"},
    }

    for router, prefix, tags in api_routers:
        app.include_router(
            router,
            prefix=f"/api/v1{prefix}",
            tags=list(tags),  # Convert Sequence[str] to list[str]
            responses=common_responses,
        )
