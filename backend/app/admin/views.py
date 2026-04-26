from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode
from uuid import UUID

from fastapi import status
from sqladmin import Admin, BaseView, ModelView, expose
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.admin.auth import AdminAuthBackend
from app.core.config import setting
from app.db.postgres import db_postgres
from app.models.admin_audit_log import AdminAuditLog
from app.models.category import Category
from app.models.delivery_shipment import DeliveryShipment
from app.models.inventory_reservation import InventoryReservation
from app.models.notification_message import NotificationMessage
from app.models.order import Order, OrderStatusEnum
from app.models.order_status_history import OrderStatusHistory
from app.models.payment_transaction import PaymentTransaction
from app.models.product import Product
from app.models.product_discount import ProductDiscount
from app.models.product_review import ProductReview
from app.models.support_message import SupportMessage
from app.models.support_ticket import (
    SupportTicket,
    SupportTicketPriorityEnum,
    SupportTicketStatusEnum,
)
from app.models.user import User
from app.models.user_login_audit_log import UserLoginAuditLog
from app.services.admin_audit_service import AdminAuditService
from app.services.support_service import SupportService


def build_support_redirect_url(ticket_id: str, **params: str) -> str:
    query_params = {"ticket_id": ticket_id, **params}
    return f"{setting.admin_base_url}/support-desk?{urlencode(query_params)}"


async def get_current_admin_user(request: Request, session) -> User | None:
    raw_admin_id = request.session.get("admin_user_id")
    if not raw_admin_id:
        return None
    return await session.get(User, UUID(str(raw_admin_id)))


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "ti ti-users"
    category = "Каталог и пользователи"
    can_create = False
    can_edit = True
    can_delete = False
    column_list = [
        User.id,
        User.email,
        User.name,
        User.avatar_image_id,
        User.role,
        User.is_active,
        User.is_blocked,
        User.email_verified_at,
        User.created_at,
        User.updated_at,
    ]
    column_searchable_list = [User.email, User.name]
    column_sortable_list = [User.email, User.name, User.created_at, User.updated_at]
    form_columns = [
        User.email,
        User.name,
        User.role,
        User.is_active,
        User.is_blocked,
        User.blocked_reason,
        User.email_verified_at,
    ]
    page_size = 50


class CategoryAdmin(ModelView, model=Category):
    name = "Категория"
    name_plural = "Категории"
    icon = "ti ti-category"
    category = "Каталог и пользователи"
    can_create = True
    can_edit = True
    can_delete = True
    column_list = [Category.id, Category.name, Category.slug, Category.updated_at]
    column_searchable_list = [Category.name, Category.slug]
    column_sortable_list = [Category.id, Category.name, Category.updated_at]
    page_size = 50


class ProductAdmin(ModelView, model=Product):
    name = "Товар"
    name_plural = "Товары"
    icon = "ti ti-shopping-bag"
    category = "Каталог и пользователи"
    can_create = True
    can_edit = True
    can_delete = False
    column_list = [
        Product.id,
        Product.sku,
        Product.name,
        Product.brand,
        Product.price,
        Product.stock,
        Product.reserved_stock,
        Product.is_active,
        Product.updated_at,
    ]
    column_searchable_list = [Product.sku, Product.name, Product.brand]
    column_sortable_list = [Product.created_at, Product.updated_at, Product.price, Product.stock]
    form_columns = [
        Product.sku,
        Product.name,
        Product.brand,
        Product.description,
        Product.price,
        Product.unit,
        Product.is_active,
        Product.photo_ids,
        Product.category_id,
        Product.stock,
        Product.reserved_stock,
    ]
    page_size = 50


class ProductDiscountAdmin(ModelView, model=ProductDiscount):
    name = "Discount"
    name_plural = "Discounts"
    icon = "ti ti-ticket"
    category = "Catalog operations"
    can_create = True
    can_edit = True
    can_delete = True
    column_list = [
        ProductDiscount.id,
        ProductDiscount.name,
        ProductDiscount.code,
        ProductDiscount.discount_type,
        ProductDiscount.value,
        ProductDiscount.is_active,
        ProductDiscount.product_id,
        ProductDiscount.category_id,
        ProductDiscount.starts_at,
        ProductDiscount.ends_at,
    ]
    column_searchable_list = [ProductDiscount.name, ProductDiscount.code]
    column_sortable_list = [
        ProductDiscount.created_at,
        ProductDiscount.updated_at,
        ProductDiscount.value,
        ProductDiscount.is_active,
    ]
    page_size = 50


class ProductReviewAdmin(ModelView, model=ProductReview):
    name = "Review"
    name_plural = "Reviews"
    icon = "ti ti-star"
    category = "Catalog operations"
    can_create = False
    can_edit = True
    can_delete = True
    column_list = [
        ProductReview.id,
        ProductReview.product_id,
        ProductReview.user_id,
        ProductReview.rating,
        ProductReview.status,
        ProductReview.author_name,
        ProductReview.created_at,
    ]
    column_searchable_list = [ProductReview.author_name, ProductReview.body, ProductReview.moderation_reason]
    column_sortable_list = [
        ProductReview.created_at,
        ProductReview.updated_at,
        ProductReview.rating,
        ProductReview.status,
    ]
    form_columns = [
        ProductReview.product_id,
        ProductReview.user_id,
        ProductReview.rating,
        ProductReview.author_name,
        ProductReview.body,
        ProductReview.status,
        ProductReview.moderation_reason,
    ]
    page_size = 50


class InventoryReservationAdmin(ModelView, model=InventoryReservation):
    name = "Inventory reservation"
    name_plural = "Inventory reservations"
    icon = "ti ti-package"
    category = "Catalog operations"
    can_create = False
    can_edit = True
    can_delete = False
    column_list = [
        InventoryReservation.id,
        InventoryReservation.order_id,
        InventoryReservation.product_id,
        InventoryReservation.quantity,
        InventoryReservation.status,
        InventoryReservation.reason,
        InventoryReservation.updated_at,
    ]
    column_sortable_list = [
        InventoryReservation.created_at,
        InventoryReservation.updated_at,
        InventoryReservation.status,
        InventoryReservation.quantity,
    ]
    page_size = 50


class OrderAdmin(ModelView, model=Order):
    name = "Заказ"
    name_plural = "Заказы"
    icon = "ti ti-receipt-2"
    category = "Продажи"
    can_create = False
    can_edit = True
    can_delete = False
    column_list = [
        Order.id,
        Order.user_id,
        Order.status,
        Order.payment_method,
        Order.payment_status,
        Order.total_amount,
        Order.created_at,
    ]
    column_sortable_list = [
        Order.created_at,
        Order.total_amount,
        Order.status,
        Order.payment_status,
    ]
    form_columns = [
        Order.status,
        Order.payment_status,
        Order.cancellation_reason,
        Order.invoice_number,
        Order.receipt_number,
        Order.delivery_method,
        Order.delivery_window_start,
        Order.delivery_window_end,
    ]
    page_size = 50


class OrderStatusHistoryAdmin(ModelView, model=OrderStatusHistory):
    name = "Order status history"
    name_plural = "Order status history"
    icon = "ti ti-history-toggle"
    category = "Sales"
    can_create = False
    can_edit = False
    can_delete = False
    column_list = [
        OrderStatusHistory.created_at,
        OrderStatusHistory.order_id,
        OrderStatusHistory.from_status,
        OrderStatusHistory.to_status,
        OrderStatusHistory.actor_user_id,
        OrderStatusHistory.reason,
    ]
    column_sortable_list = [OrderStatusHistory.created_at, OrderStatusHistory.to_status]
    page_size = 100


class PaymentTransactionAdmin(ModelView, model=PaymentTransaction):
    name = "Платёж"
    name_plural = "Платежи"
    icon = "ti ti-credit-card"
    category = "Продажи"
    can_create = False
    can_edit = False
    can_delete = False
    column_list = [
        PaymentTransaction.id,
        PaymentTransaction.order_id,
        PaymentTransaction.provider_name,
        PaymentTransaction.payment_method,
        PaymentTransaction.status,
        PaymentTransaction.amount,
        PaymentTransaction.currency,
        PaymentTransaction.processed_at,
        PaymentTransaction.created_at,
    ]
    column_sortable_list = [
        PaymentTransaction.created_at,
        PaymentTransaction.processed_at,
        PaymentTransaction.status,
        PaymentTransaction.amount,
    ]
    column_searchable_list = [
        PaymentTransaction.idempotency_key,
        PaymentTransaction.external_payment_id,
    ]
    page_size = 50


class DeliveryShipmentAdmin(ModelView, model=DeliveryShipment):
    name = "Shipment"
    name_plural = "Shipments"
    icon = "ti ti-truck-delivery"
    category = "Sales"
    can_create = False
    can_edit = True
    can_delete = False
    column_list = [
        DeliveryShipment.id,
        DeliveryShipment.order_id,
        DeliveryShipment.provider_name,
        DeliveryShipment.status,
        DeliveryShipment.tracking_number,
        DeliveryShipment.external_delivery_id,
        DeliveryShipment.updated_at,
    ]
    column_searchable_list = [DeliveryShipment.tracking_number, DeliveryShipment.external_delivery_id]
    column_sortable_list = [DeliveryShipment.created_at, DeliveryShipment.updated_at, DeliveryShipment.status]
    form_columns = [
        DeliveryShipment.status,
        DeliveryShipment.tracking_number,
        DeliveryShipment.external_delivery_id,
        DeliveryShipment.response_payload,
        DeliveryShipment.shipped_at,
        DeliveryShipment.delivered_at,
    ]
    page_size = 50


class NotificationMessageAdmin(ModelView, model=NotificationMessage):
    name = "Notification"
    name_plural = "Notifications"
    icon = "ti ti-mail"
    category = "Observability"
    can_create = False
    can_edit = True
    can_delete = False
    column_list = [
        NotificationMessage.id,
        NotificationMessage.channel,
        NotificationMessage.template_name,
        NotificationMessage.recipient,
        NotificationMessage.status,
        NotificationMessage.attempts,
        NotificationMessage.sent_at,
        NotificationMessage.created_at,
    ]
    column_searchable_list = [NotificationMessage.recipient, NotificationMessage.template_name, NotificationMessage.last_error]
    column_sortable_list = [
        NotificationMessage.created_at,
        NotificationMessage.updated_at,
        NotificationMessage.status,
        NotificationMessage.attempts,
    ]
    page_size = 100


class SupportTicketAdmin(ModelView, model=SupportTicket):
    name = "Обращение"
    name_plural = "Обращения"
    icon = "ti ti-headset"
    category = "Поддержка"
    can_create = False
    can_edit = False
    can_delete = False
    column_list = [
        SupportTicket.id,
        SupportTicket.subject,
        SupportTicket.status,
        SupportTicket.priority,
        SupportTicket.human_handoff_requested,
        SupportTicket.contact_email,
        SupportTicket.updated_at,
    ]
    column_searchable_list = [SupportTicket.subject, SupportTicket.contact_email]
    column_sortable_list = [
        SupportTicket.updated_at,
        SupportTicket.created_at,
        SupportTicket.status,
        SupportTicket.priority,
    ]
    page_size = 50


class SupportMessageAdmin(ModelView, model=SupportMessage):
    name = "Сообщение"
    name_plural = "Сообщения"
    icon = "ti ti-messages"
    category = "Поддержка"
    can_create = False
    can_edit = False
    can_delete = False
    column_list = [
        SupportMessage.id,
        SupportMessage.ticket_id,
        SupportMessage.author_type,
        SupportMessage.author_name,
        SupportMessage.created_at,
    ]
    column_searchable_list = [SupportMessage.author_name, SupportMessage.body]
    column_sortable_list = [SupportMessage.created_at, SupportMessage.author_type]
    page_size = 100


class AdminAuditLogAdmin(ModelView, model=AdminAuditLog):
    name = "Аудит"
    name_plural = "Журнал админа"
    icon = "ti ti-history"
    category = "Наблюдаемость"
    can_create = False
    can_edit = False
    can_delete = False
    column_list = [
        AdminAuditLog.created_at,
        AdminAuditLog.admin_user_id,
        AdminAuditLog.action,
        AdminAuditLog.resource_type,
        AdminAuditLog.resource_id,
        AdminAuditLog.status_code,
    ]
    column_sortable_list = [AdminAuditLog.created_at, AdminAuditLog.status_code]
    column_searchable_list = [
        AdminAuditLog.action,
        AdminAuditLog.resource_type,
        AdminAuditLog.resource_id,
    ]
    page_size = 100


class UserLoginAuditLogAdmin(ModelView, model=UserLoginAuditLog):
    name = "Login audit"
    name_plural = "Login audit"
    icon = "ti ti-login"
    category = "Observability"
    can_create = False
    can_edit = False
    can_delete = False
    column_list = [
        UserLoginAuditLog.created_at,
        UserLoginAuditLog.user_id,
        UserLoginAuditLog.email,
        UserLoginAuditLog.success,
        UserLoginAuditLog.failure_reason,
        UserLoginAuditLog.ip_address,
    ]
    column_searchable_list = [UserLoginAuditLog.email, UserLoginAuditLog.failure_reason, UserLoginAuditLog.ip_address]
    column_sortable_list = [UserLoginAuditLog.created_at, UserLoginAuditLog.success]
    page_size = 100


class SupportDeskView(BaseView):
    name = "Support Desk"
    identity = "support-desk"
    icon = "ti ti-headset"
    category = "Поддержка"

    @expose("/support-desk", methods=["GET"])
    async def support_desk(self, request: Request):
        raw_ticket_id = request.query_params.get("ticket_id")
        selected_ticket_id = None
        if raw_ticket_id:
            try:
                selected_ticket_id = UUID(raw_ticket_id)
            except ValueError:
                selected_ticket_id = None

        async with db_postgres.session_factory() as session:
            support_service = SupportService(session)
            tickets = await support_service.get_recent_active_tickets(limit=25)
            counts = await support_service.get_ticket_counts()

            selected_ticket = None
            if selected_ticket_id:
                selected_ticket = await support_service.get_ticket_by_id(selected_ticket_id)
            if selected_ticket is None and tickets:
                selected_ticket = tickets[0]

            pending_orders_result = await session.execute(
                select(Order)
                .where(
                    Order.status.in_(
                        [
                            OrderStatusEnum.CREATED,
                            OrderStatusEnum.AWAITING_PAYMENT,
                            OrderStatusEnum.PAID,
                        ]
                    )
                )
                .order_by(Order.created_at.desc())
                .limit(10)
                .options(selectinload(Order.items))
            )
            pending_orders = list(pending_orders_result.scalars().all())

            low_stock_result = await session.execute(
                select(Product)
                .where(Product.is_active.is_(True), Product.stock <= 5)
                .order_by(Product.stock.asc(), Product.updated_at.desc())
                .limit(10)
            )
            low_stock_products = list(low_stock_result.scalars().all())

        context = {
            "request": request,
            "admin_base_url": setting.admin_base_url,
            "tickets": tickets,
            "selected_ticket": selected_ticket,
            "counts": counts,
            "pending_orders": pending_orders,
            "low_stock_products": low_stock_products,
            "reply_statuses": [
                SupportTicketStatusEnum.WAITING_CUSTOMER,
                SupportTicketStatusEnum.RESOLVED,
                SupportTicketStatusEnum.CLOSED,
            ],
            "status_options": list(SupportTicketStatusEnum),
            "priority_options": list(SupportTicketPriorityEnum),
            "notice": request.query_params.get("notice"),
            "error": request.query_params.get("error"),
        }
        return await self.templates.TemplateResponse(
            request,
            "admin/support_desk.html",
            context,
        )

    @expose("/support-desk/reply/{ticket_id}", methods=["POST"])
    async def reply(self, request: Request):
        raw_ticket_id = request.path_params["ticket_id"]
        form = await request.form()
        message = str(form.get("message") or "").strip()
        raw_status = str(form.get("status") or "").strip()

        if not message:
            return RedirectResponse(
                build_support_redirect_url(raw_ticket_id, error="Пустой ответ отправить нельзя."),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        status_enum = None
        if raw_status:
            try:
                status_enum = SupportTicketStatusEnum(raw_status)
            except ValueError:
                return RedirectResponse(
                    build_support_redirect_url(raw_ticket_id, error="Передан недопустимый статус ответа."),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        async with db_postgres.session_factory() as session:
            admin_user = await get_current_admin_user(request, session)
            if admin_user is None:
                return RedirectResponse(
                    build_support_redirect_url(
                        raw_ticket_id,
                        error="Не удалось определить администратора текущей сессии.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            support_service = SupportService(session)
            try:
                ticket = await support_service.reply_as_admin(
                    ticket_id=UUID(raw_ticket_id),
                    admin_user=admin_user,
                    message=message,
                    status=status_enum,
                )
            except ValueError as exc:
                return RedirectResponse(
                    build_support_redirect_url(raw_ticket_id, error=str(exc)),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            await AdminAuditService(session).record(
                request=request,
                admin_user=admin_user,
                action="reply",
                resource_type="support_ticket",
                resource_id=str(ticket.id),
                status_code=200,
                details={"status": ticket.status.value},
            )

        return RedirectResponse(
            build_support_redirect_url(raw_ticket_id, notice="Ответ отправлен."),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    @expose("/support-desk/status/{ticket_id}", methods=["POST"])
    async def update_ticket(self, request: Request):
        raw_ticket_id = request.path_params["ticket_id"]
        form = await request.form()
        raw_status = str(form.get("ticket_status") or "").strip()
        raw_priority = str(form.get("ticket_priority") or "").strip()

        try:
            status_enum = SupportTicketStatusEnum(raw_status) if raw_status else None
            priority_enum = SupportTicketPriorityEnum(raw_priority) if raw_priority else None
        except ValueError:
            return RedirectResponse(
                build_support_redirect_url(
                    raw_ticket_id,
                    error="Переданы недопустимые значения статуса или приоритета.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        async with db_postgres.session_factory() as session:
            admin_user = await get_current_admin_user(request, session)
            support_service = SupportService(session)
            try:
                ticket = await support_service.update_ticket(
                    ticket_id=UUID(raw_ticket_id),
                    status=status_enum,
                    priority=priority_enum,
                )
            except ValueError as exc:
                return RedirectResponse(
                    build_support_redirect_url(raw_ticket_id, error=str(exc)),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            await AdminAuditService(session).record(
                request=request,
                admin_user=admin_user,
                action="update",
                resource_type="support_ticket",
                resource_id=str(ticket.id),
                status_code=200,
                details={
                    "status": ticket.status.value,
                    "priority": ticket.priority.value,
                },
            )

        return RedirectResponse(
            build_support_redirect_url(raw_ticket_id, notice="Карточка обращения обновлена."),
            status_code=status.HTTP_303_SEE_OTHER,
        )


def setup_admin(app) -> Admin:
    templates_dir = Path(__file__).resolve().parent.parent / "templates"
    authentication_backend = AdminAuthBackend(
        secret_key=setting.admin_session_secret or setting.secret_key,
    )
    admin = Admin(
        app=app,
        session_maker=db_postgres.session_factory,
        base_url=setting.admin_base_url,
        title=setting.admin_title,
        authentication_backend=authentication_backend,
        templates_dir=str(templates_dir),
    )

    admin.add_view(SupportDeskView)
    admin.add_view(UserAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(ProductDiscountAdmin)
    admin.add_view(ProductReviewAdmin)
    admin.add_view(InventoryReservationAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(OrderStatusHistoryAdmin)
    admin.add_view(PaymentTransactionAdmin)
    admin.add_view(DeliveryShipmentAdmin)
    admin.add_view(NotificationMessageAdmin)
    admin.add_view(SupportTicketAdmin)
    admin.add_view(SupportMessageAdmin)
    admin.add_view(AdminAuditLogAdmin)
    admin.add_view(UserLoginAuditLogAdmin)
    return admin
