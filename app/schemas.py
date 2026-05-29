from decimal import Decimal
from typing import Any


def money(value: Decimal) -> str:
    return f"{value:.2f}"


def user_public(user: Any) -> dict[str, Any]:
    return {"id": user.id, "email": user.email, "full_name": user.full_name}


def user_with_role(user: Any) -> dict[str, Any]:
    data = user_public(user)
    data["role"] = user.role
    return data


def account_public(account: Any) -> dict[str, Any]:
    return {"id": account.id, "user_id": account.user_id, "balance": money(account.balance)}


def payment_public(payment: Any) -> dict[str, Any]:
    return {
        "id": payment.id,
        "transaction_id": payment.transaction_id,
        "user_id": payment.user_id,
        "account_id": payment.account_id,
        "amount": money(payment.amount),
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
    }
