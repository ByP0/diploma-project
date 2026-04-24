from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.images import build_image_url, build_image_urls


class CartItemCreate(BaseModel):
    product_id: Annotated[
        UUID,
        Field(
            title="Товар",
            description="Идентификатор товара, который нужно добавить в корзину",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        ),
    ]
    quantity: Annotated[
        int,
        Field(
            title="Количество",
            description="Количество единиц товара",
            ge=1,
            examples=[2],
        ),
    ]

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "product_id": "550e8400-e29b-41d4-a716-446655440000",
                "quantity": 2,
            }
        },
    )


class CartItemUpdate(BaseModel):
    quantity: Annotated[
        int,
        Field(
            title="Количество",
            description="Новое количество товара в корзине",
            ge=1,
            examples=[3],
        ),
    ]

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "quantity": 3,
            }
        },
    )


class CartProductSummary(BaseModel):
    id: UUID
    sku: str
    name: str
    brand: str | None
    price: Decimal
    unit: str
    stock: int
    photo_ids: list[str]

    @computed_field(
        return_type=list[str],
        title="Ссылки на фотографии",
        description="Готовые ссылки на изображения товара",
    )
    @property
    def photo_urls(self) -> list[str]:
        return build_image_urls(self.photo_ids)

    @computed_field(
        return_type=str | None,
        title="Основная фотография",
        description="Первая фотография товара для отображения в корзине",
    )
    @property
    def primary_photo_url(self) -> str | None:
        if not self.photo_ids:
            return None

        return build_image_url(self.photo_ids[0])


class CartItemRead(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime
    product: CartProductSummary

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "c91f80f8-92b7-40a3-a3f8-22b7d3877eb2",
                "product_id": "550e8400-e29b-41d4-a716-446655440000",
                "quantity": 2,
                "subtotal": 9.98,
                "created_at": "2026-04-23T12:00:00Z",
                "updated_at": "2026-04-23T12:05:00Z",
                "product": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "sku": "BANAN-001",
                    "name": "Бананы органические",
                    "brand": "ФермаЭко",
                    "price": 4.99,
                    "unit": "шт",
                    "stock": 50,
                    "photo_ids": ["6622eacaf2f4b22a4eb8ac11"],
                },
            }
        },
    )


class CartRead(BaseModel):
    items: list[CartItemRead]
    total_items: int
    total_amount: Decimal

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "c91f80f8-92b7-40a3-a3f8-22b7d3877eb2",
                        "product_id": "550e8400-e29b-41d4-a716-446655440000",
                        "quantity": 2,
                        "subtotal": 9.98,
                        "created_at": "2026-04-23T12:00:00Z",
                        "updated_at": "2026-04-23T12:05:00Z",
                        "product": {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "sku": "BANAN-001",
                            "name": "Бананы органические",
                            "brand": "ФермаЭко",
                            "price": 4.99,
                            "unit": "шт",
                            "stock": 50,
                            "photo_ids": ["6622eacaf2f4b22a4eb8ac11"],
                        },
                    }
                ],
                "total_items": 2,
                "total_amount": 9.98,
            }
        }
    )
