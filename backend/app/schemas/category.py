from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryBase(BaseModel):
    id: Annotated[
        int,
        Field(
            title="Идентификатор категории",
            examples=[5],
            description="Уникальный идентификатор категории",
            ge=1,
        )
    ]


class CategoryCreate(CategoryBase):
    name: Annotated[
        str,
        Field(
            title="Название категории",
            examples=["Фрукты и овощи"],
            description="Название категории каталога",
            min_length=2,
            max_length=100,
        )
    ]

    slug: Annotated[
        str,
        Field(
            title="Символьный код категории",
            examples=["frukty-i-ovoshchi"],
            description="Уникальный символьный код категории для адресов и фильтрации",
            min_length=2,
            max_length=100,
            pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        )
    ]

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower()

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Фрукты и овощи",
                "slug": "frukty-i-ovoshchi"
            }
        }
    )


class CategoryRead(CategoryBase):
    name: Annotated[
        str,
        Field(
            title="Название категории",
            examples=["Фрукты и овощи"],
            description="Название категории каталога",
            max_length=100,
        )
    ]

    slug: Annotated[
        str,
        Field(
            title="Символьный код категории",
            examples=["frukty-i-ovoshchi"],
            description="Уникальный символьный код категории",
            max_length=100,
        )
    ]

    created_at: Annotated[
        datetime,
        Field(
            title="Дата создания",
            description="Дата и время создания категории",
            examples=["2026-04-23T12:00:00Z"],
        ),
    ]
    updated_at: Annotated[
        datetime,
        Field(
            title="Дата обновления",
            description="Дата и время последнего изменения категории",
            examples=["2026-04-23T12:30:00Z"],
        ),
    ]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Фрукты и овощи",
                "slug": "frukty-i-ovoshchi",
                "created_at": "2026-04-23T12:00:00Z",
                "updated_at": "2026-04-23T12:30:00Z",
            }
        }         
    )


class CategoryUpdate(BaseModel):
    name: Annotated[
        str | None,
        Field(
            title="Название категории",
            examples=["Фрукты и ягоды"],
            description="Новое название категории",
            min_length=2,
            max_length=100,
        )
    ] = None

    slug: Annotated[
        str | None,
        Field(
            title="Символьный код категории",
            examples=["frukty-i-yagody"],
            description="Новый символьный код категории",
            min_length=2,
            max_length=100,
            pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        )
    ] = None

    @field_validator("name")
    @classmethod
    def normalize_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()

    @field_validator("slug")
    @classmethod
    def normalize_optional_slug(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip().lower()

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Фрукты и ягоды",
                "slug": "frukty-i-yagody",
            }
        }
    )
