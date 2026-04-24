from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ImageUploadResponse(BaseModel):
    id: Annotated[
        str,
        Field(
            title="Идентификатор изображения",
            description="Идентификатор сохраненного изображения в файловом хранилище",
            examples=["6622eacaf2f4b22a4eb8ac11"],
            pattern=r"^[a-fA-F0-9]{24}$",
        ),
    ]
    url: Annotated[
        str,
        Field(
            title="Ссылка на изображение",
            description="Готовый путь для отображения изображения в интерфейсе магазина",
            examples=["/api/images/6622eacaf2f4b22a4eb8ac11"],
        ),
    ]
    filename: Annotated[
        str,
        Field(
            title="Имя файла",
            description="Исходное имя загруженного файла",
            examples=["banana.webp"],
        ),
    ]
    content_type: Annotated[
        str,
        Field(
            title="Тип содержимого",
            description="Тип содержимого изображения",
            examples=["image/webp"],
        ),
    ]
    size_bytes: Annotated[
        int,
        Field(
            title="Размер в байтах",
            description="Размер сохраненного файла",
            ge=1,
            examples=[184231],
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "6622eacaf2f4b22a4eb8ac11",
                "url": "/api/images/6622eacaf2f4b22a4eb8ac11",
                "filename": "banana.webp",
                "content_type": "image/webp",
                "size_bytes": 184231,
            }
        }
    )
