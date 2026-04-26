import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

from app.models.base import Base, BaseWithUUId

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


from app.models.category import Category
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment_transaction import PaymentTransaction
from app.models.product import Product
from app.models.product_discount import ProductDiscount
from app.models.product_review import ProductReview
from app.models.refresh_token import RefreshToken
from app.models.admin_audit_log import AdminAuditLog
from app.models.support_message import SupportMessage
from app.models.support_ticket import SupportTicket
from app.models.user import User

target_metadata = Base.metadata


def run_migrations(connection: Connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async def do_run_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(run_migrations)

    asyncio.run(do_run_migrations())


run_migrations_online()
