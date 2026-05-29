from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from sqlalchemy import select

from app.api.auth import require_roles
from app.models import Account, Payment, UserRole
from app.schemas import account_public, payment_public, user_public


bp = Blueprint("users")


@bp.get("/users/me")
@require_roles(UserRole.USER.value, UserRole.ADMIN.value)
async def me(request: Request):
    return json(user_public(request.ctx.current_user))


@bp.get("/users/me/accounts")
@require_roles(UserRole.USER.value, UserRole.ADMIN.value)
async def my_accounts(request: Request):
    result = await request.ctx.db.execute(
        select(Account).where(Account.user_id == request.ctx.current_user.id).order_by(Account.id)
    )
    return json([account_public(account) for account in result.scalars().all()])


@bp.get("/users/me/payments")
@require_roles(UserRole.USER.value, UserRole.ADMIN.value)
async def my_payments(request: Request):
    result = await request.ctx.db.execute(
        select(Payment)
        .where(Payment.user_id == request.ctx.current_user.id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
    )
    return json([payment_public(payment) for payment in result.scalars().all()])
