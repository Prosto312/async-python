from functools import wraps
from typing import Callable

import jwt
from sanic import Blueprint
from sanic.exceptions import Unauthorized
from sanic.request import Request
from sanic.response import json
from sqlalchemy import select

from app.core.security import create_access_token, decode_access_token, verify_password
from app.models import User
from app.schemas import user_with_role


bp = Blueprint("auth", url_prefix="/auth")


async def get_current_user(request: Request) -> User:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise Unauthorized("Missing bearer token")

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise Unauthorized("Invalid token") from exc

    user = await request.ctx.db.get(User, user_id)
    if user is None:
        raise Unauthorized("User not found")
    return user


def require_roles(*roles: str) -> Callable:
    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        async def wrapper(request: Request, *args, **kwargs):
            user = await get_current_user(request)
            if roles and user.role not in roles:
                raise Unauthorized("Not enough permissions")
            request.ctx.current_user = user
            return await handler(request, *args, **kwargs)

        return wrapper

    return decorator


@bp.post("/login")
async def login(request: Request):
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return json({"error": "email and password are required"}, status=400)

    result = await request.ctx.db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise Unauthorized("Invalid email or password")

    token = create_access_token(user.id, user.role)
    return json({"access_token": token, "token_type": "bearer", "user": user_with_role(user)})
