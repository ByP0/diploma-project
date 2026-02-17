from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated
from decimal import Decimal
from datetime import datetime
import uuid


class ProductBase(BaseModel):
    name: Annotated[
        str,
        Field(
            title="Product name",
            examples=["Black t-shirt Nike"],
            description="Product name",
            max_length=100,
        )
    ]

    description: Annotated[
        str,
        Field(
            title="Description",
            examples=["Black Nike T-shirt, size L, made from soft cotton. Comfortable, breathable, and keeps its shape — a clean, everyday essential with a classic fit."],
            description="Product description"
        )
    ]

    price: Annotated[
        Decimal,
        Field(
            title="Price",
            examples=[2499.99],
            description="Price tag product (Decimal type)",
            decimal_places=2
        )
    ]

    category_id: Annotated[
        int,
        Field(
            title="Categoty ID",
            examples=[5],
            description="Unique category ID"
        )
    ]

    stock: Annotated[
        int,
        Field(
            title="Stock",
            examples=[150],
            description="Quantity in stock"
        )
    ]


class ProductCreate(ProductBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Black t-shirt Nike",
                "description": "Black Nike T-shirt, size L, made from soft cotton. Comfortable, breathable, and keeps its shape — a clean, everyday essential with a classic fit.",
                "price": 2499.99,
                "category_id": 5,
                "stock": 150
            }
        }
    )


class ProductRead(ProductBase):
    id: Annotated[
        uuid.UUID,
        Field(
            title="Product ID",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
            description="Unique identifier of the product"
        )
    ]

    created_at: Annotated[
        datetime,
        Field(
            title="Created at",
            description="Timestamp when the product was created",
            examples=["2024-01-01T12:00:00Z"],
        ),
    ]

    updated_at: Annotated[
        datetime,
        Field(
            title="Updated at",
            description="Timestamp when the product was last updated",
            examples=["2024-01-02T15:30:00Z"],
        ),
    ]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Black t-shirt Nike",
                "description": "Black Nike T-shirt, size L, made from soft cotton. Comfortable, breathable, and keeps its shape — a clean, everyday essential with a classic fit.",
                "price": 2499.99,
                "category_id": 5,
                "stock": 150,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-02T15:30:00Z"
            }
        }
    )




class ProductUpdate(BaseModel):
    name: Annotated[
        str | None,
        Field(
            title="Product name",
            examples=["Black t-shirt Nike"],
            description="Product name",
            max_length=100,
        )
    ] = None

    description: Annotated[
        str | None,
        Field(
            title="Description",
            examples=["Black Nike T-shirt, size L, made from soft cotton. Comfortable, breathable, and keeps its shape — a clean, everyday essential with a classic fit."],
            description="Product description"
        )
    ] = None

    price: Annotated[
        Decimal | None,
        Field(
            title="Price",
            examples=[2499.99],
            description="Price tag product (Decimal type)",
            decimal_places=2
        )
    ] = None

    category_id: Annotated[
        int | None,
        Field(
            title="Categoty ID",
            examples=[5],
            description="Unique category ID"
        )
    ] = None

    stock: Annotated[
        int | None,
        Field(
            title="Stock",
            examples=[150],
            description="Quantity in stock"
        )
    ] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Black t-shirt Nike",
                "description": "Black Nike T-shirt, size L, made from soft cotton. Comfortable, breathable, and keeps its shape — a clean, everyday essential with a classic fit.",
                "price": 2499.99,
                "category_id": 5,
                "stock": 150
            }
        }
    )