from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    field_validator,
)

from app.core.images import build_image_url, build_image_urls
from app.models.product import ProductUnitEnum

MongoObjectId = Annotated[str, StringConstraints(pattern=r"^[a-fA-F0-9]{24}$")]
SkuStr = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9_-]{3,64}$")]


class ProductBase(BaseModel):
    sku: Annotated[
        SkuStr,
        Field(
            title="Артикул",
            description="Уникальный артикул товара",
            examples=["BANAN-001"],
        ),
    ]
    name: Annotated[
        str,
        Field(
            title="Название",
            description="Название товара для каталога",
            min_length=2,
            max_length=120,
            examples=["Бананы органические"],
        ),
    ]
    brand: Annotated[
        str | None,
        Field(
            title="Бренд",
            description="Бренд или производитель товара",
            min_length=2,
            max_length=120,
            examples=["ФермаЭко"],
        ),
    ] = None
    description: Annotated[
        str,
        Field(
            title="Описание",
            description="Подробное описание товара",
            min_length=10,
            max_length=2000,
            examples=["Свежие органические бананы из Эквадора."],
        ),
    ]
    price: Annotated[
        Decimal,
        Field(
            title="Цена",
            description="Актуальная цена товара",
            decimal_places=2,
            ge=0,
            examples=[4.99],
        ),
    ]
    unit: Annotated[
        ProductUnitEnum,
        Field(
            title="Единица измерения",
            description="Единица измерения товара",
            examples=[ProductUnitEnum.PIECE.value],
        ),
    ] = ProductUnitEnum.PIECE
    is_active: Annotated[
        bool,
        Field(
            title="Активен",
            description="Показывать ли товар в каталоге",
            examples=[True],
        ),
    ] = True
    photo_ids: Annotated[
        list[MongoObjectId],
        Field(
            title="Идентификаторы изображений",
            description="Идентификаторы изображений товара",
            examples=[["6622eacaf2f4b22a4eb8ac11", "6622eacaf2f4b22a4eb8ac12"]],
        ),
    ] = Field(default_factory=list)
    category_id: Annotated[
        int,
        Field(
            title="Идентификатор категории",
            description="Идентификатор категории товара",
            ge=1,
            examples=[5],
        ),
    ]
    stock: Annotated[
        int,
        Field(
            title="Остаток",
            description="Количество товара в наличии",
            ge=0,
            examples=[50],
        ),
    ]

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("name", "description")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("brand")
    @classmethod
    def trim_optional_brand(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()
        return value or None


class ProductCreate(ProductBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "sku": "BANAN-001",
                "name": "Бананы органические",
                "brand": "ФермаЭко",
                "description": "Свежие органические бананы из Эквадора.",
                "price": 4.99,
                "unit": ProductUnitEnum.PIECE.value,
                "is_active": True,
                "photo_ids": ["6622eacaf2f4b22a4eb8ac11"],
                "category_id": 5,
                "stock": 50,
            }
        },
    )


class ProductRead(ProductBase):
    id: Annotated[
        UUID,
        Field(
            title="Идентификатор товара",
            description="Уникальный идентификатор товара",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        ),
    ]
    created_at: Annotated[
        datetime,
        Field(
            title="Дата создания",
            description="Дата и время создания товара",
            examples=["2026-04-23T10:00:00Z"],
        ),
    ]
    updated_at: Annotated[
        datetime,
        Field(
            title="Дата обновления",
            description="Дата и время последнего обновления товара",
            examples=["2026-04-23T10:30:00Z"],
        ),
    ]

    @computed_field(
        return_type=list[str],
        title="Ссылки на изображения",
        description="Готовые ссылки на изображения для интерфейса магазина",
    )
    @property
    def photo_urls(self) -> list[str]:
        return build_image_urls(self.photo_ids)

    @computed_field(
        return_type=str | None,
        title="Основное изображение",
        description="Ссылка на первое изображение, удобная для карточек и списков товаров",
    )
    @property
    def primary_photo_url(self) -> str | None:
        if not self.photo_ids:
            return None

        return build_image_url(self.photo_ids[0])

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "sku": "BANAN-001",
                "name": "Бананы органические",
                "brand": "ФермаЭко",
                "description": "Свежие органические бананы из Эквадора.",
                "price": 4.99,
                "unit": ProductUnitEnum.PIECE.value,
                "is_active": True,
                "photo_ids": ["6622eacaf2f4b22a4eb8ac11"],
                "photo_urls": ["/api/images/6622eacaf2f4b22a4eb8ac11"],
                "primary_photo_url": "/api/images/6622eacaf2f4b22a4eb8ac11",
                "category_id": 5,
                "stock": 50,
                "created_at": "2026-04-23T10:00:00Z",
                "updated_at": "2026-04-23T10:30:00Z",
            }
        },
    )


class ProductUpdate(BaseModel):
    sku: Annotated[
        SkuStr | None,
        Field(
            title="Артикул",
            description="Новый уникальный артикул товара",
            examples=["BANAN-002"],
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            title="Название",
            description="Новое название товара",
            min_length=2,
            max_length=120,
            examples=["Бананы органические премиум"],
        ),
    ] = None
    brand: Annotated[
        str | None,
        Field(
            title="Бренд",
            description="Новый бренд или производитель товара",
            min_length=2,
            max_length=120,
            examples=["ФермаЭко Премиум"],
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            title="Описание",
            description="Новое описание товара",
            min_length=10,
            max_length=2000,
            examples=["Свежие органические бананы премиального качества."],
        ),
    ] = None
    price: Annotated[
        Decimal | None,
        Field(
            title="Цена",
            description="Новая цена товара",
            decimal_places=2,
            ge=0,
            examples=[5.49],
        ),
    ] = None
    unit: Annotated[
        ProductUnitEnum | None,
        Field(
            title="Единица измерения",
            description="Новая единица измерения товара",
            examples=[ProductUnitEnum.PIECE.value],
        ),
    ] = None
    is_active: Annotated[
        bool | None,
        Field(
            title="Активен",
            description="Нужно ли показывать товар в каталоге",
            examples=[True],
        ),
    ] = None
    photo_ids: Annotated[
        list[MongoObjectId] | None,
        Field(
            title="Идентификаторы изображений",
            description="Обновленный список идентификаторов изображений товара",
        ),
    ] = None
    category_id: Annotated[
        int | None,
        Field(
            title="Идентификатор категории",
            description="Новый идентификатор категории товара",
            ge=1,
            examples=[5],
        ),
    ] = None
    stock: Annotated[
        int | None,
        Field(
            title="Остаток",
            description="Новое количество товара в наличии",
            ge=0,
            examples=[45],
        ),
    ] = None

    @field_validator("sku")
    @classmethod
    def normalize_optional_sku(cls, value: str | None) -> str | None:
        if value is None:
            return value

        return value.strip().upper()

    @field_validator("name", "description")
    @classmethod
    def trim_optional_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return value

        return value.strip()

    @field_validator("brand")
    @classmethod
    def trim_optional_brand(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()
        return value or None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "sku": "BANAN-002",
                "name": "Бананы органические премиум",
                "brand": "ФермаЭко Премиум",
                "price": 5.49,
                "unit": ProductUnitEnum.PIECE.value,
                "is_active": True,
                "photo_ids": ["6622eacaf2f4b22a4eb8ac11"],
                "stock": 45,
            }
        },
    )
