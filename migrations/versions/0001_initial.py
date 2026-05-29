"""initial schema and seed data

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op
from passlib.context import CryptContext
import sqlalchemy as sa


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.String(length=64), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_payments_transaction_id"), "payments", ["transaction_id"], unique=True
    )

    users = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("email", sa.String),
        sa.column("full_name", sa.String),
        sa.column("password_hash", sa.String),
        sa.column("role", sa.String),
    )
    accounts = sa.table(
        "accounts",
        sa.column("id", sa.Integer),
        sa.column("user_id", sa.Integer),
        sa.column("balance", sa.Numeric),
    )

    op.bulk_insert(
        users,
        [
            {
                "id": 1,
                "email": "user@example.com",
                "full_name": "Test User",
                "password_hash": pwd_context.hash("user12345"),
                "role": "user",
            },
            {
                "id": 2,
                "email": "admin@example.com",
                "full_name": "Test Admin",
                "password_hash": pwd_context.hash("admin12345"),
                "role": "admin",
            },
        ],
    )
    op.bulk_insert(accounts, [{"id": 1, "user_id": 1, "balance": 0}])


def downgrade() -> None:
    op.drop_index(op.f("ix_payments_transaction_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_table("accounts")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
