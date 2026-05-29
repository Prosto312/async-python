from sanic import Sanic
from sanic.request import Request
from sanic.response import json

from app.api.admin import bp as admin_bp
from app.api.auth import bp as auth_bp
from app.api.payments import bp as payments_bp
from app.api.users import bp as users_bp
from app.db.session import SessionLocal, engine


def create_app() -> Sanic:
    app = Sanic("test_python_backend")

    app.blueprint(auth_bp)
    app.blueprint(users_bp)
    app.blueprint(admin_bp)
    app.blueprint(payments_bp)

    @app.get("/health")
    async def health(_request: Request):
        return json({"status": "ok"})

    @app.on_request
    async def open_db_session(request: Request):
        request.ctx.db = SessionLocal()

    @app.on_response
    async def close_db_session(request: Request, _response):
        db = getattr(request.ctx, "db", None)
        if db is not None:
            await db.close()

    @app.after_server_stop
    async def close_engine(_app: Sanic, _loop):
        await engine.dispose()

    return app
