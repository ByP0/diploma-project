from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ErrorItem(BaseModel):
    field: Annotated[
        str,
        Field(
            title="Поле",
            description="Поле или часть запроса, в которой возникла ошибка",
            examples=["тело запроса.message"],
        ),
    ]
    message: Annotated[
        str,
        Field(
            title="Описание ошибки",
            description="Пояснение, что именно не прошло проверку",
            examples=["Длина строки должна быть не меньше 1 символа."],
        ),
    ]
    error_type: Annotated[
        str,
        Field(
            title="Тип ошибки",
            description="Технический код ошибки валидации",
            examples=["string_too_short"],
        ),
    ]


class ErrorResponse(BaseModel):
    detail: Annotated[
        str,
        Field(
            title="Сообщение",
            description="Краткое описание ошибки на русском языке",
            examples=["Ошибка валидации запроса."],
        ),
    ]
    errors: Annotated[
        list[ErrorItem] | None,
        Field(
            title="Детали",
            description="Подробный список ошибок, если они есть",
        ),
    ] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Ошибка валидации запроса.",
                "errors": [
                    {
                        "field": "тело запроса.message",
                        "message": "Длина строки должна быть не меньше 1 символа.",
                        "error_type": "string_too_short",
                    }
                ],
            }
        }
    )


class MessageResponse(BaseModel):
    detail: Annotated[
        str,
        Field(
            title="Сообщение",
            description="Результат выполнения операции",
            examples=["Операция выполнена успешно."],
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Операция выполнена успешно.",
            }
        }
    )


class HealthResponse(BaseModel):
    status: Annotated[
        str,
        Field(
            title="Статус",
            description="Технический статус сервиса",
            examples=["ok"],
        ),
    ]
    detail: Annotated[
        str,
        Field(
            title="Описание",
            description="Состояние сервиса",
            examples=["Сервис работает стабильно."],
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "detail": "Сервис работает стабильно.",
            }
        }
    )
