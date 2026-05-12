"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-07 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sa.Enum('USER', 'ADMIN', 'MANAGER', 'SUPPORT', name='userroleenum').create(op.get_bind(), checkfirst=True)
    sa.Enum('CREATED', 'AWAITING_PAYMENT', 'PAID', 'PROCESSING', 'PACKED', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED', 'FAILED', name='orderstatusenum').create(op.get_bind(), checkfirst=True)
    sa.Enum('COURIER', 'EXPRESS', 'PICKUP', name='deliverymethodenum').create(op.get_bind(), checkfirst=True)
    sa.Enum('CARD_ONLINE', 'CASH_ON_DELIVERY', 'CARD_ON_DELIVERY', name='paymentmethodenum').create(op.get_bind(), checkfirst=True)
    sa.Enum('PENDING', 'SUCCEEDED', 'FAILED', 'CANCELLED', 'REFUNDED', 'PARTIALLY_REFUNDED', name='paymentstatusenum').create(op.get_bind(), checkfirst=True)
    sa.Enum('PIECE', 'KILOGRAM', 'GRAM', 'LITER', 'MILLILITER', 'PACK', name='productunitenum').create(op.get_bind(), checkfirst=True)
    sa.Enum('OPEN', 'IN_PROGRESS', 'WAITING_CUSTOMER', 'RESOLVED', 'CLOSED', name='supportticketstatusenum').create(op.get_bind(), checkfirst=True)
    sa.Enum('LOW', 'NORMAL', 'HIGH', 'URGENT', name='supportticketpriorityenum').create(op.get_bind(), checkfirst=True)
    sa.Enum('CUSTOMER', 'AI', 'ADMIN', name='supportmessageauthorenum').create(op.get_bind(), checkfirst=True)

    op.create_table(
        'categories',
        sa.Column('id', sa.SmallInteger(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('slug'),
    )

    op.create_table(
        'inbox_messages',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_name', sa.String(length=128), nullable=False),
        sa.Column('source', sa.String(length=128), nullable=False),
        sa.Column('consumer_name', sa.String(length=128), nullable=False),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dead_lettered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.String(length=1000), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('event_id', 'consumer_name', name='uq_inbox_messages_event_id_consumer'),
    )

    op.create_table(
        'notification_messages',
        sa.Column('channel', sa.String(length=32), nullable=False, server_default='email'),
        sa.Column('template_name', sa.String(length=64), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body_text', sa.String(length=5000), nullable=False),
        sa.Column('body_html', sa.String(length=10000), nullable=True),
        sa.Column('context_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='queued'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('provider_name', sa.String(length=64), nullable=True),
        sa.Column('last_error', sa.String(length=1000), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('attempts >= 0', name='ck_notification_messages_attempts_non_negative'),
        sa.CheckConstraint('max_attempts > 0', name='ck_notification_messages_max_attempts_positive'),
    )

    op.create_table(
        'outbox_messages',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_name', sa.String(length=128), nullable=False),
        sa.Column('event_kind', sa.String(length=32), nullable=False),
        sa.Column('aggregate_type', sa.String(length=64), nullable=False),
        sa.Column('aggregate_id', sa.String(length=255), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('causation_id', sa.String(length=255), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('destination', sa.String(length=32), nullable=False, server_default='local'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('exchange_name', sa.String(length=255), nullable=True),
        sa.Column('routing_key', sa.String(length=255), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dead_lettered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.String(length=1000), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('event_id', name='uq_outbox_messages_event_id'),
    )

    op.create_table(
        'users',
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('avatar_image_id', sa.String(length=24), nullable=True),
        sa.Column('hashed_password', sa.Text(), nullable=False),
        sa.Column('role', postgresql.ENUM('USER', 'ADMIN', 'MANAGER', 'SUPPORT', name='userroleenum', create_type=False), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('blocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('blocked_reason', sa.String(length=500), nullable=True),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token_hash', sa.String(length=255), nullable=True),
        sa.Column('password_reset_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verification_token_hash', sa.String(length=255), nullable=True),
        sa.Column('email_verification_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('email'),
    )

    op.create_table(
        'admin_audit_logs',
        sa.Column('admin_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('request_method', sa.String(length=10), nullable=False),
        sa.Column('request_path', sa.String(length=255), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'delivery_addresses',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('label', sa.String(length=64), nullable=True),
        sa.Column('recipient_name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=32), nullable=False),
        sa.Column('line1', sa.String(length=255), nullable=False),
        sa.Column('line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=128), nullable=False),
        sa.Column('region', sa.String(length=128), nullable=True),
        sa.Column('postal_code', sa.String(length=32), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=False, server_default='RU'),
        sa.Column('floor', sa.String(length=32), nullable=True),
        sa.Column('apartment', sa.String(length=32), nullable=True),
        sa.Column('entrance', sa.String(length=32), nullable=True),
        sa.Column('intercom', sa.String(length=64), nullable=True),
        sa.Column('instructions', sa.String(length=1000), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'orders',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', postgresql.ENUM('CREATED', 'AWAITING_PAYMENT', 'PAID', 'PROCESSING', 'PACKED', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED', 'FAILED', name='orderstatusenum', create_type=False), nullable=False, server_default='CREATED'),
        sa.Column('items_total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('delivery_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('price_locked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('customer_phone', sa.String(length=32), nullable=True),
        sa.Column('customer_comment', sa.String(length=1000), nullable=True),
        sa.Column('delivery_method', postgresql.ENUM('COURIER', 'EXPRESS', 'PICKUP', name='deliverymethodenum', create_type=False), nullable=False, server_default='COURIER'),
        sa.Column('delivery_window_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_window_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_address_line1', sa.String(length=255), nullable=True),
        sa.Column('delivery_address_line2', sa.String(length=255), nullable=True),
        sa.Column('delivery_city', sa.String(length=128), nullable=True),
        sa.Column('delivery_region', sa.String(length=128), nullable=True),
        sa.Column('delivery_postal_code', sa.String(length=32), nullable=True),
        sa.Column('delivery_country', sa.String(length=2), nullable=False, server_default='RU'),
        sa.Column('delivery_floor', sa.String(length=32), nullable=True),
        sa.Column('delivery_apartment', sa.String(length=32), nullable=True),
        sa.Column('delivery_entrance', sa.String(length=32), nullable=True),
        sa.Column('delivery_intercom', sa.String(length=64), nullable=True),
        sa.Column('delivery_instructions', sa.String(length=1000), nullable=True),
        sa.Column('payment_method', postgresql.ENUM('CARD_ONLINE', 'CASH_ON_DELIVERY', 'CARD_ON_DELIVERY', name='paymentmethodenum', create_type=False), nullable=False, server_default='CARD_ONLINE'),
        sa.Column('payment_status', postgresql.ENUM('PENDING', 'SUCCEEDED', 'FAILED', 'CANCELLED', 'REFUNDED', 'PARTIALLY_REFUNDED', name='paymentstatusenum', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='RUB'),
        sa.Column('cancellation_reason', sa.String(length=1000), nullable=True),
        sa.Column('invoice_number', sa.String(length=64), nullable=True),
        sa.Column('receipt_number', sa.String(length=64), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('char_length(currency) = 3', name='ck_orders_currency_length'),
        sa.CheckConstraint('delivery_cost >= 0', name='ck_orders_delivery_cost_non_negative'),
        sa.CheckConstraint('delivery_window_end IS NULL OR delivery_window_start IS NULL OR delivery_window_end > delivery_window_start', name='ck_orders_delivery_window_valid'),
        sa.CheckConstraint('items_total_amount >= 0', name='ck_orders_items_total_amount_non_negative'),
        sa.CheckConstraint('total_amount >= 0', name='ck_orders_total_amount_non_negative'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'products',
        sa.Column('sku', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('brand', sa.String(length=120), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('unit', postgresql.ENUM('PIECE', 'KILOGRAM', 'GRAM', 'LITER', 'MILLILITER', 'PACK', name='productunitenum', create_type=False), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('photo_ids', postgresql.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column('category_id', sa.SmallInteger(), nullable=False),
        sa.Column('stock', sa.Integer(), nullable=False),
        sa.Column('reserved_stock', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('price >= 0', name='ck_products_price_non_negative'),
        sa.CheckConstraint('reserved_stock >= 0', name='ck_products_reserved_stock_non_negative'),
        sa.CheckConstraint('stock >= 0', name='ck_products_stock_non_negative'),
        sa.CheckConstraint('stock >= reserved_stock', name='ck_products_stock_gte_reserved'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.UniqueConstraint('sku', name='uq_products_sku'),
    )

    op.create_table(
        'refresh_token',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hashed_token', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('expires_at > created_at', name='ck_refresh_token_expires_after_create'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'support_tickets',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_admin_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contact_email', sa.Text(), nullable=True),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('status', postgresql.ENUM('OPEN', 'IN_PROGRESS', 'WAITING_CUSTOMER', 'RESOLVED', 'CLOSED', name='supportticketstatusenum', create_type=False), nullable=False, server_default='OPEN'),
        sa.Column('priority', postgresql.ENUM('LOW', 'NORMAL', 'HIGH', 'URGENT', name='supportticketpriorityenum', create_type=False), nullable=False, server_default='NORMAL'),
        sa.Column('human_handoff_requested', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('ai_last_used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('last_message_preview', sa.String(length=280), nullable=False, server_default=sa.text("''")),
        sa.Column('last_customer_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_admin_reply_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['assigned_admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'user_login_audit_logs',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=32), nullable=False, server_default='login'),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'cart_items',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('guest_cart_id', sa.String(length=64), nullable=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('(user_id IS NOT NULL AND guest_cart_id IS NULL) OR (user_id IS NULL AND guest_cart_id IS NOT NULL)', name='ck_cart_items_owner'),
        sa.CheckConstraint('quantity > 0', name='ck_cart_items_quantity_positive'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'delivery_shipments',
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_name', sa.String(length=64), nullable=False),
        sa.Column('delivery_method', postgresql.ENUM('COURIER', 'EXPRESS', 'PICKUP', name='deliverymethodenum', create_type=False), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='created'),
        sa.Column('quoted_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('external_delivery_id', sa.String(length=255), nullable=True),
        sa.Column('tracking_number', sa.String(length=64), nullable=True),
        sa.Column('request_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('quoted_cost >= 0', name='ck_delivery_shipments_quoted_cost_non_negative'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'inventory_reservations',
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('reason', sa.String(length=64), nullable=False, server_default='order'),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('quantity > 0', name='ck_inventory_reservations_quantity_positive'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'order_items',
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('product_name', sa.Text(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('returned_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('line_total', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('line_total >= 0', name='ck_order_items_line_total_non_negative'),
        sa.CheckConstraint('quantity > 0', name='ck_order_items_quantity_positive'),
        sa.CheckConstraint('returned_quantity <= quantity', name='ck_order_items_returned_quantity_lte_quantity'),
        sa.CheckConstraint('returned_quantity >= 0', name='ck_order_items_returned_quantity_non_negative'),
        sa.CheckConstraint('unit_price >= 0', name='ck_order_items_unit_price_non_negative'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'order_status_history',
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_status', sa.String(length=32), nullable=True),
        sa.Column('to_status', sa.String(length=32), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_role', sa.String(length=32), nullable=True),
        sa.Column('reason', sa.String(length=1000), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'payment_transactions',
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider_name', sa.String(length=64), nullable=False),
        sa.Column('operation_type', sa.String(length=32), nullable=False, server_default='payment_intent'),
        sa.Column('payment_method', postgresql.ENUM('CARD_ONLINE', 'CASH_ON_DELIVERY', 'CARD_ON_DELIVERY', name='paymentmethodenum', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'SUCCEEDED', 'FAILED', 'CANCELLED', 'REFUNDED', 'PARTIALLY_REFUNDED', name='paymentstatusenum', create_type=False), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('external_payment_id', sa.String(length=255), nullable=True),
        sa.Column('redirect_url', sa.String(length=512), nullable=True),
        sa.Column('failure_code', sa.String(length=64), nullable=True),
        sa.Column('failure_reason', sa.String(length=1000), nullable=True),
        sa.Column('request_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('amount >= 0', name='ck_payment_transactions_amount_non_negative'),
        sa.CheckConstraint('char_length(currency) = 3', name='ck_payment_transactions_currency_length'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_transaction_id'], ['payment_transactions.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('idempotency_key', name='uq_payment_transactions_idempotency_key'),
    )

    op.create_table(
        'product_discounts',
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=True),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('discount_type', sa.String(length=16), nullable=False, server_default='percent'),
        sa.Column('value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('category_id', sa.SmallInteger(), nullable=True),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("discount_type != 'percent' OR value <= 100", name='ck_product_discounts_percent_lte_100'),
        sa.CheckConstraint("discount_type IN ('percent', 'fixed')", name='ck_product_discounts_type'),
        sa.CheckConstraint('ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at', name='ck_product_discounts_period_valid'),
        sa.CheckConstraint('usage_limit IS NULL OR usage_limit >= 0', name='ck_product_discounts_usage_limit_non_negative'),
        sa.CheckConstraint('used_count >= 0', name='ck_product_discounts_used_count_non_negative'),
        sa.CheckConstraint('value >= 0', name='ck_product_discounts_value_non_negative'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('code', name='uq_product_discounts_code'),
    )

    op.create_table(
        'product_reviews',
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('author_name', sa.String(length=255), nullable=True),
        sa.Column('body', sa.String(length=3000), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('moderation_reason', sa.String(length=1000), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='ck_product_reviews_status'),
        sa.CheckConstraint('rating BETWEEN 1 AND 5', name='ck_product_reviews_rating_range'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'support_messages',
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_type', postgresql.ENUM('CUSTOMER', 'AI', 'ADMIN', name='supportmessageauthorenum', create_type=False), nullable=False),
        sa.Column('author_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('author_name', sa.String(length=255), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['author_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_inbox_messages_consumer_name', 'inbox_messages', ['consumer_name'], unique=False)
    op.create_index('ix_inbox_messages_created_at', 'inbox_messages', ['created_at'], unique=False)
    op.create_index('ix_inbox_messages_source', 'inbox_messages', ['source'], unique=False)
    op.create_index('ix_inbox_messages_status', 'inbox_messages', ['status'], unique=False)
    op.create_index('ix_notification_messages_next_retry_at', 'notification_messages', ['next_retry_at'], unique=False)
    op.create_index('ix_notification_messages_status', 'notification_messages', ['status'], unique=False)
    op.create_index('ix_notification_messages_template_name', 'notification_messages', ['template_name'], unique=False)
    op.create_index('ix_outbox_messages_created_at', 'outbox_messages', ['created_at'], unique=False)
    op.create_index('ix_outbox_messages_destination', 'outbox_messages', ['destination'], unique=False)
    op.create_index('ix_outbox_messages_event_name', 'outbox_messages', ['event_name'], unique=False)
    op.create_index('ix_outbox_messages_next_retry_at', 'outbox_messages', ['next_retry_at'], unique=False)
    op.create_index('ix_outbox_messages_status', 'outbox_messages', ['status'], unique=False)
    op.create_index('ix_admin_audit_logs_action', 'admin_audit_logs', ['action'], unique=False)
    op.create_index('ix_admin_audit_logs_admin_user_id', 'admin_audit_logs', ['admin_user_id'], unique=False)
    op.create_index('ix_admin_audit_logs_created_at', 'admin_audit_logs', ['created_at'], unique=False)
    op.create_index('ix_admin_audit_logs_resource_type', 'admin_audit_logs', ['resource_type'], unique=False)
    op.create_index('ix_delivery_addresses_is_default', 'delivery_addresses', ['is_default'], unique=False)
    op.create_index('ix_delivery_addresses_user_id', 'delivery_addresses', ['user_id'], unique=False)
    op.create_index('ix_orders_user_id', 'orders', ['user_id'], unique=False)
    op.create_index('ix_products_category_id', 'products', ['category_id'], unique=False)
    op.create_index('ix_refresh_token_expires_at', 'refresh_token', ['expires_at'], unique=False)
    op.create_index('ix_refresh_token_revoked', 'refresh_token', ['revoked'], unique=False)
    op.create_index('ix_refresh_token_user_id', 'refresh_token', ['user_id'], unique=False)
    op.create_index('ix_support_tickets_assigned_admin_id', 'support_tickets', ['assigned_admin_id'], unique=False)
    op.create_index('ix_support_tickets_human_handoff_requested', 'support_tickets', ['human_handoff_requested'], unique=False)
    op.create_index('ix_support_tickets_priority', 'support_tickets', ['priority'], unique=False)
    op.create_index('ix_support_tickets_status', 'support_tickets', ['status'], unique=False)
    op.create_index('ix_support_tickets_user_id', 'support_tickets', ['user_id'], unique=False)
    op.create_index('ix_user_login_audit_logs_created_at', 'user_login_audit_logs', ['created_at'], unique=False)
    op.create_index('ix_user_login_audit_logs_email', 'user_login_audit_logs', ['email'], unique=False)
    op.create_index('ix_user_login_audit_logs_success', 'user_login_audit_logs', ['success'], unique=False)
    op.create_index('ix_user_login_audit_logs_user_id', 'user_login_audit_logs', ['user_id'], unique=False)
    op.create_index('ix_cart_items_guest_cart_id', 'cart_items', ['guest_cart_id'], unique=False)
    op.create_index('ix_cart_items_product_id', 'cart_items', ['product_id'], unique=False)
    op.create_index('ix_cart_items_user_id', 'cart_items', ['user_id'], unique=False)
    op.create_index('uq_cart_items_guest_product', 'cart_items', ['guest_cart_id', 'product_id'], unique=True)
    op.create_index('uq_cart_items_user_product', 'cart_items', ['user_id', 'product_id'], unique=True)
    op.create_index('ix_delivery_shipments_external_delivery_id', 'delivery_shipments', ['external_delivery_id'], unique=False)
    op.create_index('ix_delivery_shipments_order_id', 'delivery_shipments', ['order_id'], unique=False)
    op.create_index('ix_delivery_shipments_status', 'delivery_shipments', ['status'], unique=False)
    op.create_index('ix_delivery_shipments_tracking_number', 'delivery_shipments', ['tracking_number'], unique=False)
    op.create_index('ix_inventory_reservations_order_id', 'inventory_reservations', ['order_id'], unique=False)
    op.create_index('ix_inventory_reservations_product_id', 'inventory_reservations', ['product_id'], unique=False)
    op.create_index('ix_inventory_reservations_status', 'inventory_reservations', ['status'], unique=False)
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'], unique=False)
    op.create_index('ix_order_status_history_order_id', 'order_status_history', ['order_id'], unique=False)
    op.create_index('ix_order_status_history_to_status', 'order_status_history', ['to_status'], unique=False)
    op.create_index('ix_payment_transactions_external_payment_id', 'payment_transactions', ['external_payment_id'], unique=False)
    op.create_index('ix_payment_transactions_order_id', 'payment_transactions', ['order_id'], unique=False)
    op.create_index('ix_payment_transactions_provider_name', 'payment_transactions', ['provider_name'], unique=False)
    op.create_index('ix_payment_transactions_status', 'payment_transactions', ['status'], unique=False)
    op.create_index('ix_product_discounts_category_id', 'product_discounts', ['category_id'], unique=False)
    op.create_index('ix_product_discounts_ends_at', 'product_discounts', ['ends_at'], unique=False)
    op.create_index('ix_product_discounts_is_active', 'product_discounts', ['is_active'], unique=False)
    op.create_index('ix_product_discounts_product_id', 'product_discounts', ['product_id'], unique=False)
    op.create_index('ix_product_discounts_starts_at', 'product_discounts', ['starts_at'], unique=False)
    op.create_index('ix_product_reviews_product_id', 'product_reviews', ['product_id'], unique=False)
    op.create_index('ix_product_reviews_rating', 'product_reviews', ['rating'], unique=False)
    op.create_index('ix_product_reviews_status', 'product_reviews', ['status'], unique=False)
    op.create_index('ix_product_reviews_user_id', 'product_reviews', ['user_id'], unique=False)
    op.create_index('ix_support_messages_author_type', 'support_messages', ['author_type'], unique=False)
    op.create_index('ix_support_messages_author_user_id', 'support_messages', ['author_user_id'], unique=False)
    op.create_index('ix_support_messages_ticket_id', 'support_messages', ['ticket_id'], unique=False)


def downgrade() -> None:
    op.drop_table('support_messages')
    op.drop_table('product_reviews')
    op.drop_table('product_discounts')
    op.drop_table('payment_transactions')
    op.drop_table('order_status_history')
    op.drop_table('order_items')
    op.drop_table('inventory_reservations')
    op.drop_table('delivery_shipments')
    op.drop_table('cart_items')
    op.drop_table('user_login_audit_logs')
    op.drop_table('support_tickets')
    op.drop_table('refresh_token')
    op.drop_table('products')
    op.drop_table('orders')
    op.drop_table('delivery_addresses')
    op.drop_table('admin_audit_logs')
    op.drop_table('users')
    op.drop_table('outbox_messages')
    op.drop_table('notification_messages')
    op.drop_table('inbox_messages')
    op.drop_table('categories')

    sa.Enum('CUSTOMER', 'AI', 'ADMIN', name='supportmessageauthorenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum('LOW', 'NORMAL', 'HIGH', 'URGENT', name='supportticketpriorityenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum('OPEN', 'IN_PROGRESS', 'WAITING_CUSTOMER', 'RESOLVED', 'CLOSED', name='supportticketstatusenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum('PIECE', 'KILOGRAM', 'GRAM', 'LITER', 'MILLILITER', 'PACK', name='productunitenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum('PENDING', 'SUCCEEDED', 'FAILED', 'CANCELLED', 'REFUNDED', 'PARTIALLY_REFUNDED', name='paymentstatusenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum('CARD_ONLINE', 'CASH_ON_DELIVERY', 'CARD_ON_DELIVERY', name='paymentmethodenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum('COURIER', 'EXPRESS', 'PICKUP', name='deliverymethodenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum('CREATED', 'AWAITING_PAYMENT', 'PAID', 'PROCESSING', 'PACKED', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED', 'FAILED', name='orderstatusenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum('USER', 'ADMIN', 'MANAGER', 'SUPPORT', name='userroleenum').drop(op.get_bind(), checkfirst=True)
