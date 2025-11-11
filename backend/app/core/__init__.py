"""Core application assembly utilities.

This package provides a minimal app factory and supporting modules to keep
`main.py` lean while avoiding over‑engineering. The goal is clarity:

create_app() -> FastAPI instance with:
  - lifespan management (background tasks, redis, rate limiter)
  - middleware registration (correlation, sanitization, request logging)
  - router inclusion (versioned under /api/v1)
  - exception handlers

All behavior matches the previous static `app` in `main.py`.
"""
