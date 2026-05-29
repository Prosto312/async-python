from decimal import Decimal, InvalidOperation

from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from sqlalchemy.exc import IntegrityError

from app.core.security import build_payment_signature
from app.models import Account, Payment, User
from app.schemas import payment_public


bp = Blueprint("payments", url_prefix="/payments")


@bp.post("/webhook")
async def payment_webhook(request: Request):
    data = request.json or {}
    required = {"transaction_id", "account_id", "user_id", "amount", "signature"}
    if missing := required - data.keys():
        return json({"error": f"missing fields: {', '.join(sorted(missing))}"}, status=400)

    try:
        account_id = int(data["account_id"])
        user_id = int(data["user_id"])
        amount = Decimal(str(data["amount"]))
    except (ValueError, InvalidOperation):
        return json({"error": "account_id, user_id and amount must be valid"}, status=400)

    if amount <= 0:
        return json({"error": "amount must be positive"}, status=400)

    expected_signature = build_payment_signature(
        account_id=account_id,
        amount=data["amount"],
        transaction_id=str(data["transaction_id"]),
        user_id=user_id,
    )
    if data["signature"] != expected_signature:
        return json({"error": "invalid signature"}, status=400)

    user = await request.ctx.db.get(User, user_id)
    if user is None:
        return json({"error": "user not found"}, status=404)

    account = await request.ctx.db.get(Account, account_id)
    if account is None:
        account = Account(id=account_id, user_id=user_id, balance=Decimal("0.00"))
        request.ctx.db.add(account)
        await request.ctx.db.flush()
    elif account.user_id != user_id:
        return json({"error": "account does not belong to user"}, status=400)

    payment = Payment(
        transaction_id=str(data["transaction_id"]),
        account_id=account.id,
        user_id=user_id,
        amount=amount,
    )
    request.ctx.db.add(payment)
    account.balance += amount

    try:
        await request.ctx.db.commit()
    except IntegrityError:
        await request.ctx.db.rollback()
        return json({"error": "transaction already processed"}, status=409)

    await request.ctx.db.refresh(payment)
    await request.ctx.db.refresh(account)
    result = payment_public(payment)
    result["account_balance"] = f"{account.balance:.2f}"
    return json(result, status=201)
