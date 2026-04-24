from __future__ import annotations

from fastapi import status

from app.schemas.common import ErrorResponse, MessageResponse


ERROR_DESCRIPTIONS = {
    status.HTTP_400_BAD_REQUEST: "Некорректный запрос.",
    status.HTTP_401_UNAUTHORIZED: "Требуется аутентификация.",
    status.HTTP_403_FORBIDDEN: "Недостаточно прав для выполнения действия.",
    status.HTTP_404_NOT_FOUND: "Запрошенный ресурс не найден.",
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: "Загруженный файл слишком большой.",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "Неподдерживаемый тип содержимого.",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "Ошибка валидации запроса.",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Внутренняя ошибка сервера.",
}


def build_error_responses(*codes: int) -> dict[int, dict[str, object]]:
    return {
        code: {
            "model": ErrorResponse,
            "description": ERROR_DESCRIPTIONS[code],
        }
        for code in codes
    }


def message_response(description: str) -> dict[str, object]:
    return {
        "model": MessageResponse,
        "description": description,
    }
