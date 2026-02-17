from pydantic import BaseModel, ConfigDict,Field
from typing import Annotated 
from datetime import datetime 


class CategoryBase(BaseModel):
    id: Annotated[
        int,
        Field(
            title="Categoty ID",
            examples=[5],
            description="Unique category ID"
        )
    ]


class CategoryCreate(CategoryBase):
    name: Annotated[
        str,
        Field(
            title="Category name",
            examples=["T-shirt"],
            description="Unique category name",
            max_length=100,
        )
    ]

    slug: Annotated[
        str,
        Field(
            title="Category slug",
            examples=["t-shirt"],
            description="Unique category name",
            max_length=100
        )
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "T-shirt",
                "slug": "t-shirt"
            }
        }
    )


class CategoryRead(CategoryBase):
    name: Annotated[
        str,
        Field(
            title="Category name",
            examples=["T-shirt"],
            description="Unique category name",
            max_length=100,
        )
    ]

    slug: Annotated[
        str,
        Field(
            title="Category slug",
            examples=["t-shirt"],
            description="Unique category name",
            max_length=100
        )
    ]

    created_at: Annotated[
        datetime,
        Field(
            title="Created at",
            description="Timestamp when the category was created",
            examples=["2024-01-01T12:00:00Z"],
        ),
    ]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examle": {
                "id": 1,
                "name": "T-shirt",
                "slug": "t-shirt",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }         
    )


class CategoryUpdate(BaseModel):
    id: Annotated[
        int | None,
        Field(
            title="Categoty ID",
            examples=[5],
            description="Unique category ID"
        )
    ] = None

    name: Annotated[
        str | None,
        Field(
            title="Category name",
            examples=["T-shirt"],
            description="Unique category name",
            max_length=100,
        )
    ] = None

    slug: Annotated[
        str | None,
        Field(
            title="Category slug",
            examples=["t-shirt"],
            description="Unique category name",
            max_length=100
        )
    ] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "T-shirt",
                "slug": "t-shirt",
            }
        }
    )