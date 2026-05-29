from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.auth import require_roles
from app.core.security import hash_password
from app.models import User, UserRole
from app.schemas import account_public, user_with_role


bp = Blueprint("admin", url_prefix="/admin")


def user_admin_public(user: User) -> dict:
    data = user_with_role(user)
    data["accounts"] = [account_public(account) for account in user.accounts]
    return data


async def _create_user(request: Request):
    data = request.json or {}
    required = {"email", "password", "full_name"}
    if missing := required - data.keys():
        return json({"error": f"missing fields: {', '.join(sorted(missing))}"}, status=400)

    user = User(
        email=data["email"],
        full_name=data["full_name"],
        password_hash=hash_password(data["password"]),
        role=data.get("role", UserRole.USER.value),
    )
    if user.role not in {UserRole.USER.value, UserRole.ADMIN.value}:
        return json({"error": "role must be user or admin"}, status=400)

    request.ctx.db.add(user)
    try:
        await request.ctx.db.commit()
    except IntegrityError:
        await request.ctx.db.rollback()
        return json({"error": "email already exists"}, status=409)
    await request.ctx.db.refresh(user)
    return json(user_with_role(user))


async def _list_users(request: Request):
    result = await request.ctx.db.execute(
        select(User).options(selectinload(User.accounts)).order_by(User.id)
    )
    return json([user_admin_public(user) for user in result.scalars().all()])


@bp.route("/users", methods=["GET", "POST"])
@require_roles(UserRole.ADMIN.value)
async def users_collection(request: Request):
    if request.method == "POST":
        return await _create_user(request)
    return await _list_users(request)


async def _get_user(request: Request, user_id: int):
    result = await request.ctx.db.execute(
        select(User).options(selectinload(User.accounts)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return json({"error": "user not found"}, status=404)
    return json(user_admin_public(user))


async def _update_user(request: Request, user_id: int):
    user = await request.ctx.db.get(User, user_id)
    if user is None:
        return json({"error": "user not found"}, status=404)

    data = request.json or {}
    if "email" in data:
        user.email = data["email"]
    if "full_name" in data:
        user.full_name = data["full_name"]
    if "password" in data:
        user.password_hash = hash_password(data["password"])
    if "role" in data:
        if data["role"] not in {UserRole.USER.value, UserRole.ADMIN.value}:
            return json({"error": "role must be user or admin"}, status=400)
        user.role = data["role"]

    try:
        await request.ctx.db.commit()
    except IntegrityError:
        await request.ctx.db.rollback()
        return json({"error": "email already exists"}, status=409)
    await request.ctx.db.refresh(user)
    return json(user_with_role(user), status=201)


async def _delete_user(request: Request, user_id: int):
    if request.ctx.current_user.id == user_id:
        return json({"error": "admin cannot delete itself"}, status=400)

    user = await request.ctx.db.get(User, user_id)
    if user is None:
        return json({"error": "user not found"}, status=404)

    await request.ctx.db.delete(user)
    await request.ctx.db.commit()
    return json({"status": "deleted"})


@bp.route("/users/<user_id:int>", methods=["GET", "PATCH", "DELETE"])
@require_roles(UserRole.ADMIN.value)
async def users_item(request: Request, user_id: int):
    if request.method == "GET":
        return await _get_user(request, user_id)
    if request.method == "PATCH":
        return await _update_user(request, user_id)
    return await _delete_user(request, user_id)
