"""finalize backend domains

Revision ID: 1f7c2d4b9a11
Revises: b7c2d1e4f903
Create Date: 2026-04-24 18:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1f7c2d4b9a11"
down_revision: Union[str, Sequence[str], None] = "b7c2d1e4f903"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    delivery_method_enum = postgresql.ENUM(
        "COURIER",
        "EXPRESS",
        "PICKUP",
        name="deliverymethodenum",
        create_type=False,
    )
    delivery_method_enum.create(op.get_bind(), checkfirst=True)

    op.execute("ALTER TYPE userroleenum ADD VALUE IF NOT EXISTS 'MANAGER'")
    op.execute("ALTER TYPE userroleenum ADD VALUE IF NOT EXISTS 'SUPPORT'")
    op.execute("ALTER TYPE orderstatusenum ADD VALUE IF NOT EXISTS 'CREATED'")
    op.execute("ALTER TYPE orderstatusenum ADD VALUE IF NOT EXISTS 'AWAITING_PAYMENT'")
    op.execute("ALTER TYPE orderstatusenum ADD VALUE IF NOT EXISTS 'PROCESSING'")
    op.execute("ALTER TYPE orderstatusenum ADD VALUE IF NOT EXISTS 'PACKED'")
    op.execute("ALTER TYPE orderstatusenum ADD VALUE IF NOT EXISTS 'SHIPPED'")
    op.execute("ALTER TYPE orderstatusenum ADD VALUE IF NOT EXISTS 'REFUNDED'")
    op.execute("ALTER TYPE orderstatusenum ADD VALUE IF NOT EXISTS 'FAILED'")
    op.execute("ALTER TYPE paymentstatusenum ADD VALUE IF NOT EXISTS 'REFUNDED'")
    op.execute("ALTER TYPE paymentstatusenum ADD VALUE IF NOT EXISTS 'PARTIALLY_REFUNDED'")

    op.add_column("users", sa.Column("is_active", sa.BOOLEAN(), nullable=False, server_default=sa.text("true")))
    op.add_column("users", sa.Column("is_blocked", sa.BOOLEAN(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("blocked_at", postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("users", sa.Column("blocked_reason", sa.VARCHAR(length=500), nullable=True))
    op.add_column("users", sa.Column("email_verified_at", postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("users", sa.Column("password_reset_token_hash", sa.VARCHAR(length=255), nullable=True))
    op.add_column("users", sa.Column("password_reset_expires_at", postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("users", sa.Column("password_reset_requested_at", postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("users", sa.Column("email_verification_token_hash", sa.VARCHAR(length=255), nullable=True))
    op.add_column("users", sa.Column("email_verification_expires_at", postgresql.TIMESTAMP(timezone=True), nullable=True))

    op.create_table(
        "user_login_audit_logs",
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("email", sa.VARCHAR(length=255), nullable=False),
        sa.Column("event_type", sa.VARCHAR(length=32), nullable=False, server_default="login"),
        sa.Column("success", sa.BOOLEAN(), nullable=False),
        sa.Column("failure_reason", sa.VARCHAR(length=255), nullable=True),
        sa.Column("ip_address", sa.VARCHAR(length=64), nullable=True),
        sa.Column("user_agent", sa.VARCHAR(length=512), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_login_audit_logs_user_id", "user_login_audit_logs", ["user_id"], unique=False)
    op.create_index("ix_user_login_audit_logs_email", "user_login_audit_logs", ["email"], unique=False)
    op.create_index("ix_user_login_audit_logs_success", "user_login_audit_logs", ["success"], unique=False)
    op.create_index("ix_user_login_audit_logs_created_at", "user_login_audit_logs", ["created_at"], unique=False)

    op.add_column("products", sa.Column("reserved_stock", sa.INTEGER(), nullable=False, server_default="0"))
    op.create_check_constraint("ck_products_reserved_stock_non_negative", "products", "reserved_stock >= 0")
    op.create_check_constraint("ck_products_stock_gte_reserved", "products", "stock >= reserved_stock")

    op.drop_constraint("uq_cart_items_user_product", "cart_items", type_="unique")
    op.alter_column("cart_items", "user_id", existing_type=sa.UUID(), nullable=True)
    op.add_column("cart_items", sa.Column("guest_cart_id", sa.VARCHAR(length=64), nullable=True))
    op.add_column("cart_items", sa.Column("expires_at", postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.execute("UPDATE cart_items SET expires_at = now() + interval '10 day' WHERE expires_at IS NULL")
    op.alter_column("cart_items", "expires_at", existing_type=postgresql.TIMESTAMP(timezone=True), nullable=False)
    op.create_index(op.f("ix_cart_items_guest_cart_id"), "cart_items", ["guest_cart_id"], unique=False)
    op.create_check_constraint(
        "ck_cart_items_owner",
        "cart_items",
        "(user_id IS NOT NULL AND guest_cart_id IS NULL) OR (user_id IS NULL AND guest_cart_id IS NOT NULL)",
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_cart_items_user_product ON cart_items (user_id, product_id) WHERE guest_cart_id IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_cart_items_guest_product ON cart_items (guest_cart_id, product_id) WHERE user_id IS NULL"
    )

    op.execute("UPDATE orders SET status = 'CREATED' WHERE status = 'PENDING'")
    op.execute("UPDATE orders SET status = 'PROCESSING' WHERE status = 'CONFIRMED'")
    op.execute("UPDATE orders SET status = 'SHIPPED' WHERE status = 'OUT_FOR_DELIVERY'")
    op.execute("ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'CREATED'")

    op.add_column("orders", sa.Column("items_total_amount", sa.NUMERIC(precision=10, scale=2), nullable=True))
    op.add_column("orders", sa.Column("delivery_cost", sa.NUMERIC(precision=10, scale=2), nullable=True))
    op.add_column("orders", sa.Column("price_locked_at", postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("cancellation_reason", sa.VARCHAR(length=1000), nullable=True))
    op.add_column("orders", sa.Column("invoice_number", sa.VARCHAR(length=64), nullable=True))
    op.add_column("orders", sa.Column("receipt_number", sa.VARCHAR(length=64), nullable=True))
    op.execute("UPDATE orders SET items_total_amount = total_amount WHERE items_total_amount IS NULL")
    op.execute("UPDATE orders SET delivery_cost = 0 WHERE delivery_cost IS NULL")
    op.execute("UPDATE orders SET price_locked_at = created_at WHERE price_locked_at IS NULL")
    op.alter_column("orders", "items_total_amount", existing_type=sa.NUMERIC(precision=10, scale=2), nullable=False)
    op.alter_column("orders", "delivery_cost", existing_type=sa.NUMERIC(precision=10, scale=2), nullable=False)
    op.alter_column("orders", "price_locked_at", existing_type=postgresql.TIMESTAMP(timezone=True), nullable=False)
    op.create_check_constraint("ck_orders_items_total_amount_non_negative", "orders", "items_total_amount >= 0")
    op.create_check_constraint("ck_orders_delivery_cost_non_negative", "orders", "delivery_cost >= 0")

    op.add_column("order_items", sa.Column("returned_quantity", sa.INTEGER(), nullable=False, server_default="0"))
    op.create_check_constraint("ck_order_items_returned_quantity_non_negative", "order_items", "returned_quantity >= 0")
    op.create_check_constraint("ck_order_items_returned_quantity_lte_quantity", "order_items", "returned_quantity <= quantity")

    op.add_column("payment_transactions", sa.Column("parent_transaction_id", sa.UUID(), nullable=True))
    op.add_column(
        "payment_transactions",
        sa.Column("operation_type", sa.VARCHAR(length=32), nullable=False, server_default="payment_intent"),
    )
    op.create_foreign_key(
        "fk_payment_transactions_parent_transaction_id",
        "payment_transactions",
        "payment_transactions",
        ["parent_transaction_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_payment_transactions_external_payment_id",
        "payment_transactions",
        ["external_payment_id"],
        unique=False,
    )

    op.create_table(
        "order_status_history",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("from_status", sa.VARCHAR(length=32), nullable=True),
        sa.Column("to_status", sa.VARCHAR(length=32), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("actor_role", sa.VARCHAR(length=32), nullable=True),
        sa.Column("reason", sa.VARCHAR(length=1000), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_status_history_order_id", "order_status_history", ["order_id"], unique=False)
    op.create_index("ix_order_status_history_to_status", "order_status_history", ["to_status"], unique=False)

    op.create_table(
        "inventory_reservations",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.INTEGER(), nullable=False),
        sa.Column("status", sa.VARCHAR(length=32), nullable=False, server_default="active"),
        sa.Column("reason", sa.VARCHAR(length=64), nullable=False, server_default="order"),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_reservations_quantity_positive"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_reservations_order_id", "inventory_reservations", ["order_id"], unique=False)
    op.create_index("ix_inventory_reservations_product_id", "inventory_reservations", ["product_id"], unique=False)
    op.create_index("ix_inventory_reservations_status", "inventory_reservations", ["status"], unique=False)

    op.create_table(
        "delivery_addresses",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("label", sa.VARCHAR(length=64), nullable=True),
        sa.Column("recipient_name", sa.VARCHAR(length=255), nullable=False),
        sa.Column("phone", sa.VARCHAR(length=32), nullable=False),
        sa.Column("line1", sa.VARCHAR(length=255), nullable=False),
        sa.Column("line2", sa.VARCHAR(length=255), nullable=True),
        sa.Column("city", sa.VARCHAR(length=128), nullable=False),
        sa.Column("region", sa.VARCHAR(length=128), nullable=True),
        sa.Column("postal_code", sa.VARCHAR(length=32), nullable=True),
        sa.Column("country", sa.VARCHAR(length=2), nullable=False, server_default="RU"),
        sa.Column("floor", sa.VARCHAR(length=32), nullable=True),
        sa.Column("apartment", sa.VARCHAR(length=32), nullable=True),
        sa.Column("entrance", sa.VARCHAR(length=32), nullable=True),
        sa.Column("intercom", sa.VARCHAR(length=64), nullable=True),
        sa.Column("instructions", sa.VARCHAR(length=1000), nullable=True),
        sa.Column("is_default", sa.BOOLEAN(), nullable=False, server_default=sa.text("false")),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_delivery_addresses_user_id", "delivery_addresses", ["user_id"], unique=False)
    op.create_index("ix_delivery_addresses_is_default", "delivery_addresses", ["is_default"], unique=False)

    op.create_table(
        "delivery_shipments",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("provider_name", sa.VARCHAR(length=64), nullable=False),
        sa.Column("delivery_method", delivery_method_enum, nullable=False),
        sa.Column("status", sa.VARCHAR(length=32), nullable=False, server_default="created"),
        sa.Column("quoted_cost", sa.NUMERIC(precision=10, scale=2), nullable=False),
        sa.Column("external_delivery_id", sa.VARCHAR(length=255), nullable=True),
        sa.Column("tracking_number", sa.VARCHAR(length=64), nullable=True),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("shipped_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("delivered_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("quoted_cost >= 0", name="ck_delivery_shipments_quoted_cost_non_negative"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_delivery_shipments_order_id", "delivery_shipments", ["order_id"], unique=False)
    op.create_index("ix_delivery_shipments_status", "delivery_shipments", ["status"], unique=False)
    op.create_index(
        "ix_delivery_shipments_external_delivery_id",
        "delivery_shipments",
        ["external_delivery_id"],
        unique=False,
    )
    op.create_index("ix_delivery_shipments_tracking_number", "delivery_shipments", ["tracking_number"], unique=False)

    op.create_table(
        "notification_messages",
        sa.Column("channel", sa.VARCHAR(length=32), nullable=False, server_default="email"),
        sa.Column("template_name", sa.VARCHAR(length=64), nullable=False),
        sa.Column("recipient", sa.VARCHAR(length=255), nullable=False),
        sa.Column("subject", sa.VARCHAR(length=255), nullable=False),
        sa.Column("body_text", sa.VARCHAR(length=5000), nullable=False),
        sa.Column("body_html", sa.VARCHAR(length=10000), nullable=True),
        sa.Column("context_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.VARCHAR(length=32), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.INTEGER(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.INTEGER(), nullable=False, server_default="3"),
        sa.Column("provider_name", sa.VARCHAR(length=64), nullable=True),
        sa.Column("last_error", sa.VARCHAR(length=1000), nullable=True),
        sa.Column("next_retry_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("sent_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("attempts >= 0", name="ck_notification_messages_attempts_non_negative"),
        sa.CheckConstraint("max_attempts > 0", name="ck_notification_messages_max_attempts_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_messages_status", "notification_messages", ["status"], unique=False)
    op.create_index("ix_notification_messages_next_retry_at", "notification_messages", ["next_retry_at"], unique=False)
    op.create_index("ix_notification_messages_template_name", "notification_messages", ["template_name"], unique=False)

    op.create_table(
        "product_discounts",
        sa.Column("name", sa.VARCHAR(length=120), nullable=False),
        sa.Column("code", sa.VARCHAR(length=64), nullable=True),
        sa.Column("description", sa.VARCHAR(length=1000), nullable=True),
        sa.Column("discount_type", sa.VARCHAR(length=16), nullable=False, server_default="percent"),
        sa.Column("value", sa.NUMERIC(precision=10, scale=2), nullable=False),
        sa.Column("is_active", sa.BOOLEAN(), nullable=False, server_default=sa.text("true")),
        sa.Column("product_id", sa.UUID(), nullable=True),
        sa.Column("category_id", sa.SMALLINT(), nullable=True),
        sa.Column("starts_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ends_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("usage_limit", sa.INTEGER(), nullable=True),
        sa.Column("used_count", sa.INTEGER(), nullable=False, server_default="0"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("discount_type IN ('percent', 'fixed')", name="ck_product_discounts_type"),
        sa.CheckConstraint("value >= 0", name="ck_product_discounts_value_non_negative"),
        sa.CheckConstraint("discount_type != 'percent' OR value <= 100", name="ck_product_discounts_percent_lte_100"),
        sa.CheckConstraint(
            "usage_limit IS NULL OR usage_limit >= 0",
            name="ck_product_discounts_usage_limit_non_negative",
        ),
        sa.CheckConstraint("used_count >= 0", name="ck_product_discounts_used_count_non_negative"),
        sa.CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_product_discounts_period_valid",
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_product_discounts_code"),
    )
    op.create_index("ix_product_discounts_product_id", "product_discounts", ["product_id"], unique=False)
    op.create_index("ix_product_discounts_category_id", "product_discounts", ["category_id"], unique=False)
    op.create_index("ix_product_discounts_is_active", "product_discounts", ["is_active"], unique=False)
    op.create_index("ix_product_discounts_starts_at", "product_discounts", ["starts_at"], unique=False)
    op.create_index("ix_product_discounts_ends_at", "product_discounts", ["ends_at"], unique=False)

    op.create_table(
        "product_reviews",
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("rating", sa.INTEGER(), nullable=False),
        sa.Column("author_name", sa.VARCHAR(length=255), nullable=True),
        sa.Column("body", sa.VARCHAR(length=3000), nullable=False),
        sa.Column("status", sa.VARCHAR(length=32), nullable=False, server_default="pending"),
        sa.Column("moderation_reason", sa.VARCHAR(length=1000), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_product_reviews_rating_range"),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_product_reviews_status"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_reviews_product_id", "product_reviews", ["product_id"], unique=False)
    op.create_index("ix_product_reviews_user_id", "product_reviews", ["user_id"], unique=False)
    op.create_index("ix_product_reviews_status", "product_reviews", ["status"], unique=False)
    op.create_index("ix_product_reviews_rating", "product_reviews", ["rating"], unique=False)

    op.create_table(
        "outbox_messages",
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("event_name", sa.VARCHAR(length=128), nullable=False),
        sa.Column("event_kind", sa.VARCHAR(length=32), nullable=False),
        sa.Column("aggregate_type", sa.VARCHAR(length=64), nullable=False),
        sa.Column("aggregate_id", sa.VARCHAR(length=255), nullable=True),
        sa.Column("version", sa.INTEGER(), nullable=False),
        sa.Column("correlation_id", sa.VARCHAR(length=255), nullable=True),
        sa.Column("causation_id", sa.VARCHAR(length=255), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.VARCHAR(length=32), nullable=False, server_default="pending"),
        sa.Column("destination", sa.VARCHAR(length=32), nullable=False, server_default="local"),
        sa.Column("attempts", sa.INTEGER(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.INTEGER(), nullable=False, server_default="5"),
        sa.Column("exchange_name", sa.VARCHAR(length=255), nullable=True),
        sa.Column("routing_key", sa.VARCHAR(length=255), nullable=True),
        sa.Column("next_retry_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("published_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("processed_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("dead_lettered_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_error", sa.VARCHAR(length=1000), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_outbox_messages_event_id"),
    )
    op.create_index("ix_outbox_messages_status", "outbox_messages", ["status"], unique=False)
    op.create_index("ix_outbox_messages_destination", "outbox_messages", ["destination"], unique=False)
    op.create_index("ix_outbox_messages_event_name", "outbox_messages", ["event_name"], unique=False)
    op.create_index("ix_outbox_messages_next_retry_at", "outbox_messages", ["next_retry_at"], unique=False)
    op.create_index("ix_outbox_messages_created_at", "outbox_messages", ["created_at"], unique=False)

    op.create_table(
        "inbox_messages",
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("event_name", sa.VARCHAR(length=128), nullable=False),
        sa.Column("source", sa.VARCHAR(length=128), nullable=False),
        sa.Column("consumer_name", sa.VARCHAR(length=128), nullable=False),
        sa.Column("correlation_id", sa.VARCHAR(length=255), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.VARCHAR(length=32), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.INTEGER(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.INTEGER(), nullable=False, server_default="5"),
        sa.Column("processed_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("dead_lettered_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_error", sa.VARCHAR(length=1000), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "consumer_name", name="uq_inbox_messages_event_id_consumer"),
    )
    op.create_index("ix_inbox_messages_status", "inbox_messages", ["status"], unique=False)
    op.create_index("ix_inbox_messages_source", "inbox_messages", ["source"], unique=False)
    op.create_index("ix_inbox_messages_consumer_name", "inbox_messages", ["consumer_name"], unique=False)
    op.create_index("ix_inbox_messages_created_at", "inbox_messages", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_inbox_messages_created_at", table_name="inbox_messages")
    op.drop_index("ix_inbox_messages_consumer_name", table_name="inbox_messages")
    op.drop_index("ix_inbox_messages_source", table_name="inbox_messages")
    op.drop_index("ix_inbox_messages_status", table_name="inbox_messages")
    op.drop_table("inbox_messages")

    op.drop_index("ix_outbox_messages_created_at", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_next_retry_at", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_event_name", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_destination", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_status", table_name="outbox_messages")
    op.drop_table("outbox_messages")

    op.drop_index("ix_notification_messages_template_name", table_name="notification_messages")
    op.drop_index("ix_notification_messages_next_retry_at", table_name="notification_messages")
    op.drop_index("ix_notification_messages_status", table_name="notification_messages")
    op.drop_table("notification_messages")

    op.drop_index("ix_product_reviews_rating", table_name="product_reviews")
    op.drop_index("ix_product_reviews_status", table_name="product_reviews")
    op.drop_index("ix_product_reviews_user_id", table_name="product_reviews")
    op.drop_index("ix_product_reviews_product_id", table_name="product_reviews")
    op.drop_table("product_reviews")

    op.drop_index("ix_product_discounts_ends_at", table_name="product_discounts")
    op.drop_index("ix_product_discounts_starts_at", table_name="product_discounts")
    op.drop_index("ix_product_discounts_is_active", table_name="product_discounts")
    op.drop_index("ix_product_discounts_category_id", table_name="product_discounts")
    op.drop_index("ix_product_discounts_product_id", table_name="product_discounts")
    op.drop_table("product_discounts")

    op.drop_index("ix_delivery_shipments_tracking_number", table_name="delivery_shipments")
    op.drop_index("ix_delivery_shipments_external_delivery_id", table_name="delivery_shipments")
    op.drop_index("ix_delivery_shipments_status", table_name="delivery_shipments")
    op.drop_index("ix_delivery_shipments_order_id", table_name="delivery_shipments")
    op.drop_table("delivery_shipments")

    op.drop_index("ix_delivery_addresses_is_default", table_name="delivery_addresses")
    op.drop_index("ix_delivery_addresses_user_id", table_name="delivery_addresses")
    op.drop_table("delivery_addresses")

    op.drop_index("ix_inventory_reservations_status", table_name="inventory_reservations")
    op.drop_index("ix_inventory_reservations_product_id", table_name="inventory_reservations")
    op.drop_index("ix_inventory_reservations_order_id", table_name="inventory_reservations")
    op.drop_table("inventory_reservations")

    op.drop_index("ix_order_status_history_to_status", table_name="order_status_history")
    op.drop_index("ix_order_status_history_order_id", table_name="order_status_history")
    op.drop_table("order_status_history")

    op.drop_index("ix_payment_transactions_external_payment_id", table_name="payment_transactions")
    op.drop_constraint("fk_payment_transactions_parent_transaction_id", "payment_transactions", type_="foreignkey")
    op.drop_column("payment_transactions", "operation_type")
    op.drop_column("payment_transactions", "parent_transaction_id")

    op.drop_constraint("ck_order_items_returned_quantity_lte_quantity", "order_items", type_="check")
    op.drop_constraint("ck_order_items_returned_quantity_non_negative", "order_items", type_="check")
    op.drop_column("order_items", "returned_quantity")

    op.drop_constraint("ck_orders_delivery_cost_non_negative", "orders", type_="check")
    op.drop_constraint("ck_orders_items_total_amount_non_negative", "orders", type_="check")
    op.drop_column("orders", "receipt_number")
    op.drop_column("orders", "invoice_number")
    op.drop_column("orders", "cancellation_reason")
    op.drop_column("orders", "price_locked_at")
    op.drop_column("orders", "delivery_cost")
    op.drop_column("orders", "items_total_amount")

    op.execute("DROP INDEX IF EXISTS uq_cart_items_guest_product")
    op.execute("DROP INDEX IF EXISTS uq_cart_items_user_product")
    op.drop_constraint("ck_cart_items_owner", "cart_items", type_="check")
    op.drop_index(op.f("ix_cart_items_guest_cart_id"), table_name="cart_items")
    op.drop_column("cart_items", "expires_at")
    op.drop_column("cart_items", "guest_cart_id")
    op.alter_column("cart_items", "user_id", existing_type=sa.UUID(), nullable=False)
    op.create_unique_constraint("uq_cart_items_user_product", "cart_items", ["user_id", "product_id"])

    op.drop_constraint("ck_products_stock_gte_reserved", "products", type_="check")
    op.drop_constraint("ck_products_reserved_stock_non_negative", "products", type_="check")
    op.drop_column("products", "reserved_stock")

    op.drop_index("ix_user_login_audit_logs_created_at", table_name="user_login_audit_logs")
    op.drop_index("ix_user_login_audit_logs_success", table_name="user_login_audit_logs")
    op.drop_index("ix_user_login_audit_logs_email", table_name="user_login_audit_logs")
    op.drop_index("ix_user_login_audit_logs_user_id", table_name="user_login_audit_logs")
    op.drop_table("user_login_audit_logs")

    op.drop_column("users", "email_verification_expires_at")
    op.drop_column("users", "email_verification_token_hash")
    op.drop_column("users", "password_reset_requested_at")
    op.drop_column("users", "password_reset_expires_at")
    op.drop_column("users", "password_reset_token_hash")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "blocked_reason")
    op.drop_column("users", "blocked_at")
    op.drop_column("users", "is_blocked")
    op.drop_column("users", "is_active")
