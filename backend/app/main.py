from backend.app.core.factory import create_app

# Single application instance (retains previous import path: backend.app.main:app)
app = create_app()
