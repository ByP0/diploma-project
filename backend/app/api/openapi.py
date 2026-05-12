from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


API_TITLE = "Интернет-магазин продуктовых товаров"
API_DESCRIPTION = (
    "REST API для интернет-магазина продуктовых товаров. "
    "Документация сгруппирована по основным сценариям: каталог, корзина, оформление заказов, "
    "платежи, доставка, уведомления, поддержка и административные операции."
)

OPENAPI_TAGS = [
    {
        "name": "Авторизация",
        "description": "Регистрация, вход, обновление токенов, выход и сервисные операции с паролем и email.",
    },
    {
        "name": "Пользователи",
        "description": "Профиль текущего пользователя, аватар, аудит входов и управление доступом пользователей.",
    },
    {
        "name": "Категории",
        "description": "Публичный просмотр категорий каталога и административное управление категориями.",
    },
    {
        "name": "Товары",
        "description": "Публичный каталог товаров, фильтрация, карточки товаров и административное управление ассортиментом.",
    },
    {
        "name": "Медиа",
        "description": "Загрузка, получение и удаление изображений товаров.",
    },
    {
        "name": "Корзина",
        "description": "Корзины авторизованных пользователей и гостевые корзины с управлением позициями.",
    },
    {
        "name": "Оформление заказа",
        "description": "Предварительный расчет состава заказа перед созданием заказа из корзины.",
    },
    {
        "name": "Заказы",
        "description": "Создание заказов, история покупателя, документы, повтор заказа и административное управление статусами.",
    },
    {
        "name": "Платежи",
        "description": "Повторная проверка платежей и прием подписанных вебхуков платежного провайдера.",
    },
    {
        "name": "Доставка",
        "description": "Расчет доставки, адреса пользователя и обработка вебхуков службы доставки.",
    },
    {
        "name": "Уведомления",
        "description": "Административный просмотр сообщений и ручная обработка очереди уведомлений.",
    },
    {
        "name": "Поддержка",
        "description": "Чат-бот поддержки, обращения пользователей и рабочее место оператора поддержки.",
    },
    {
        "name": "Сервис",
        "description": "Служебные проверки состояния приложения.",
    },
]


@dataclass(frozen=True)
class OperationDoc:
    tag: str
    summary: str
    description: str


OPERATION_DOCS: dict[tuple[str, str], OperationDoc] = {
    ("GET", "/health"): OperationDoc(
        "Сервис",
        "Проверить состояние сервиса",
        "Возвращает простой статус доступности приложения для внешних проверок и ручной диагностики.",
    ),
    ("POST", "/api/auth/register"): OperationDoc(
        "Авторизация",
        "Зарегистрировать пользователя",
        "Создает учетную запись покупателя по email, паролю и необязательному имени. Возвращает данные созданного пользователя.",
    ),
    ("POST", "/api/auth/login"): OperationDoc(
        "Авторизация",
        "Войти в систему",
        "Проверяет email и пароль, выдает cookie с access и refresh токенами и устанавливает CSRF cookie для защищенных запросов.",
    ),
    ("POST", "/api/auth/refresh"): OperationDoc(
        "Авторизация",
        "Обновить токены",
        "Читает refresh token из cookie, выпускает новую пару токенов и обновляет авторизационные cookie.",
    ),
    ("POST", "/api/auth/logout"): OperationDoc(
        "Авторизация",
        "Выйти из системы",
        "Отзывает текущий refresh token, если он есть, и очищает авторизационные cookie пользователя.",
    ),
    ("POST", "/api/auth/password/recover"): OperationDoc(
        "Авторизация",
        "Запросить восстановление пароля",
        "Принимает email пользователя и регистрирует запрос на восстановление пароля.",
    ),
    ("POST", "/api/auth/password/reset"): OperationDoc(
        "Авторизация",
        "Сбросить пароль",
        "Проверяет токен восстановления и устанавливает новый пароль пользователя.",
    ),
    ("POST", "/api/auth/email-verification/request"): OperationDoc(
        "Авторизация",
        "Запросить подтверждение email",
        "Регистрирует stub-запрос на подтверждение email. В этой сборке отправка письма может быть отключена.",
    ),
    ("POST", "/api/auth/email-verification/confirm"): OperationDoc(
        "Авторизация",
        "Подтвердить email",
        "Принимает token подтверждения email. Сейчас подтверждение намеренно отключено и возвращает служебное сообщение.",
    ),
    ("GET", "/api/users/me"): OperationDoc(
        "Пользователи",
        "Получить свой профиль",
        "Возвращает профиль текущего авторизованного пользователя.",
    ),
    ("PATCH", "/api/users/me"): OperationDoc(
        "Пользователи",
        "Обновить свой профиль",
        "Позволяет изменить имя пользователя и при необходимости сменить пароль с проверкой текущего пароля.",
    ),
    ("POST", "/api/users/me/avatar"): OperationDoc(
        "Пользователи",
        "Загрузить свой аватар",
        "Принимает файл изображения и привязывает его как аватар текущего пользователя.",
    ),
    ("DELETE", "/api/users/me/avatar"): OperationDoc(
        "Пользователи",
        "Удалить свой аватар",
        "Удаляет привязку аватара у текущего пользователя и возвращает обновленный профиль.",
    ),
    ("GET", "/api/users/login-audit"): OperationDoc(
        "Пользователи",
        "Получить аудит входов",
        "Возвращает журнал попыток входа с фильтрами по пользователю, email, успешности, типу события, IP и датам.",
    ),
    ("GET", "/api/users"): OperationDoc(
        "Пользователи",
        "Получить список пользователей",
        "Административный метод для поиска и фильтрации пользователей по роли, активности, блокировке и подтверждению email.",
    ),
    ("PATCH", "/api/users/{user_id}/access"): OperationDoc(
        "Пользователи",
        "Обновить доступ пользователя",
        "Административно меняет роль, активность, блокировку и связанные параметры доступа выбранного пользователя.",
    ),
    ("GET", "/api/categories"): OperationDoc(
        "Категории",
        "Получить список категорий",
        "Возвращает страницу категорий каталога с пагинацией. Результат кешируется для ускорения каталога.",
    ),
    ("GET", "/api/categories/{category_id}"): OperationDoc(
        "Категории",
        "Получить категорию",
        "Возвращает категорию каталога по числовому идентификатору.",
    ),
    ("POST", "/api/categories"): OperationDoc(
        "Категории",
        "Создать категорию",
        "Административно создает категорию каталога с заданными идентификатором, названием и slug.",
    ),
    ("PUT", "/api/categories/{category_id}"): OperationDoc(
        "Категории",
        "Обновить категорию",
        "Административно меняет название или slug существующей категории и очищает кеш каталога.",
    ),
    ("DELETE", "/api/categories/{category_id}"): OperationDoc(
        "Категории",
        "Удалить категорию",
        "Административно удаляет категорию, если бизнес-правила сервиса разрешают удаление.",
    ),
    ("GET", "/api/products"): OperationDoc(
        "Товары",
        "Получить список товаров",
        "Возвращает товары каталога с фильтрами по категории, диапазону цены, поисковой строке и активности.",
    ),
    ("GET", "/api/products/{product_id}"): OperationDoc(
        "Товары",
        "Получить товар",
        "Возвращает карточку товара по UUID, включая данные категории, остаток и ссылки на изображения.",
    ),
    ("POST", "/api/products"): OperationDoc(
        "Товары",
        "Создать товар",
        "Административно создает товар с артикулом, названием, ценой, категорией, остатком и изображениями.",
    ),
    ("PUT", "/api/products/{product_id}"): OperationDoc(
        "Товары",
        "Обновить товар",
        "Административно обновляет поля товара и сбрасывает кеш каталога.",
    ),
    ("DELETE", "/api/products/{product_id}"): OperationDoc(
        "Товары",
        "Удалить товар",
        "Административно удаляет товар из каталога по UUID.",
    ),
    ("POST", "/api/images"): OperationDoc(
        "Медиа",
        "Загрузить изображение",
        "Административно загружает изображение в файловое хранилище и возвращает его идентификатор, URL и метаданные.",
    ),
    ("GET", "/api/images/{image_id}"): OperationDoc(
        "Медиа",
        "Получить изображение",
        "Отдает бинарное содержимое изображения по идентификатору из хранилища.",
    ),
    ("DELETE", "/api/images/{image_id}"): OperationDoc(
        "Медиа",
        "Удалить изображение",
        "Административно удаляет изображение и отвязывает его от товаров, где оно использовалось.",
    ),
    ("POST", "/api/cart/guest/sessions"): OperationDoc(
        "Корзина",
        "Создать гостевую корзину",
        "Создает идентификатор гостевой корзины, которую можно использовать без авторизации.",
    ),
    ("GET", "/api/cart"): OperationDoc(
        "Корзина",
        "Получить свою корзину",
        "Возвращает корзину текущего авторизованного пользователя.",
    ),
    ("POST", "/api/cart/items"): OperationDoc(
        "Корзина",
        "Добавить товар в свою корзину",
        "Добавляет товар в корзину текущего пользователя или увеличивает количество существующей позиции.",
    ),
    ("PUT", "/api/cart/items/{product_id}"): OperationDoc(
        "Корзина",
        "Изменить позицию своей корзины",
        "Обновляет количество выбранного товара в корзине текущего пользователя.",
    ),
    ("DELETE", "/api/cart/items/{product_id}"): OperationDoc(
        "Корзина",
        "Удалить позицию из своей корзины",
        "Удаляет товар из корзины текущего пользователя.",
    ),
    ("DELETE", "/api/cart"): OperationDoc(
        "Корзина",
        "Очистить свою корзину",
        "Удаляет все позиции из корзины текущего пользователя.",
    ),
    ("GET", "/api/cart/guest/{guest_cart_id}"): OperationDoc(
        "Корзина",
        "Получить гостевую корзину",
        "Возвращает состав гостевой корзины по ее идентификатору.",
    ),
    ("POST", "/api/cart/guest/{guest_cart_id}/items"): OperationDoc(
        "Корзина",
        "Добавить товар в гостевую корзину",
        "Добавляет товар в гостевую корзину или увеличивает количество существующей позиции.",
    ),
    ("PUT", "/api/cart/guest/{guest_cart_id}/items/{product_id}"): OperationDoc(
        "Корзина",
        "Изменить позицию гостевой корзины",
        "Обновляет количество выбранного товара в гостевой корзине.",
    ),
    ("DELETE", "/api/cart/guest/{guest_cart_id}/items/{product_id}"): OperationDoc(
        "Корзина",
        "Удалить позицию из гостевой корзины",
        "Удаляет товар из гостевой корзины.",
    ),
    ("DELETE", "/api/cart/guest/{guest_cart_id}"): OperationDoc(
        "Корзина",
        "Очистить гостевую корзину",
        "Удаляет все позиции из гостевой корзины.",
    ),
    ("POST", "/api/checkout/preview"): OperationDoc(
        "Оформление заказа",
        "Предварительно рассчитать заказ",
        "Проверяет данные оформления и возвращает предварительный расчет заказа до фактического создания.",
    ),
    ("POST", "/api/orders/from-cart"): OperationDoc(
        "Заказы",
        "Создать заказ из корзины",
        "Создает заказ для текущего пользователя на основе корзины и данных оформления.",
    ),
    ("POST", "/api/orders/{order_id}/payments/retry"): OperationDoc(
        "Заказы",
        "Повторить платеж по заказу",
        "Повторно инициирует платеж по заказу текущего пользователя с поддержкой Idempotency-Key.",
    ),
    ("POST", "/api/orders/{order_id}/payments/sync"): OperationDoc(
        "Заказы",
        "Синхронизировать платеж заказа",
        "Запрашивает актуальный платежный статус заказа текущего пользователя и обновляет заказ.",
    ),
    ("GET", "/api/orders"): OperationDoc(
        "Заказы",
        "Получить историю заказов",
        "Возвращает страницу заказов текущего пользователя.",
    ),
    ("GET", "/api/orders/{order_id}"): OperationDoc(
        "Заказы",
        "Получить свой заказ",
        "Возвращает заказ текущего пользователя по UUID.",
    ),
    ("POST", "/api/orders/{order_id}/cancel"): OperationDoc(
        "Заказы",
        "Отменить свой заказ",
        "Отменяет заказ текущего пользователя, если его состояние допускает отмену.",
    ),
    ("POST", "/api/orders/{order_id}/refund"): OperationDoc(
        "Заказы",
        "Запросить возврат по заказу",
        "Запускает возврат платежа по заказу текущего пользователя с указанной причиной.",
    ),
    ("POST", "/api/orders/{order_id}/repeat"): OperationDoc(
        "Заказы",
        "Повторить заказ",
        "Переносит товары из выбранного заказа в текущую корзину пользователя.",
    ),
    ("GET", "/api/orders/{order_id}/documents/{document_type}"): OperationDoc(
        "Заказы",
        "Получить документ заказа",
        "Формирует счет или чек по заказу текущего пользователя. Тип документа: invoice или receipt.",
    ),
    ("GET", "/api/orders/management/list"): OperationDoc(
        "Заказы",
        "Получить все заказы",
        "Административный список заказов с пагинацией для панели управления.",
    ),
    ("GET", "/api/orders/management/{order_id}"): OperationDoc(
        "Заказы",
        "Получить заказ для администратора",
        "Административно возвращает заказ по UUID независимо от владельца заказа.",
    ),
    ("PATCH", "/api/orders/{order_id}/status"): OperationDoc(
        "Заказы",
        "Обновить статус заказа",
        "Административно меняет статус заказа и сохраняет запись аудита с причиной изменения.",
    ),
    ("POST", "/api/orders/management/{order_id}/cancel"): OperationDoc(
        "Заказы",
        "Отменить заказ администратором",
        "Административно отменяет заказ и фиксирует действие в аудите.",
    ),
    ("POST", "/api/payments/orders/{order_id}/recheck"): OperationDoc(
        "Платежи",
        "Перепроверить платеж заказа",
        "Синхронизирует платежный статус заказа текущего пользователя через платежный сервис.",
    ),
    ("POST", "/api/payments/webhooks/{provider_name}"): OperationDoc(
        "Платежи",
        "Принять вебхук платежа",
        "Обрабатывает подписанный вебхук платежного провайдера и обновляет транзакцию по внешнему идентификатору.",
    ),
    ("POST", "/api/delivery/quote"): OperationDoc(
        "Доставка",
        "Рассчитать стоимость доставки",
        "Возвращает предложение по доставке: провайдера, метод, стоимость, валюту, срок и дополнительные детали.",
    ),
    ("GET", "/api/delivery/addresses"): OperationDoc(
        "Доставка",
        "Получить адреса доставки",
        "Возвращает сохраненные адреса доставки текущего пользователя.",
    ),
    ("POST", "/api/delivery/addresses"): OperationDoc(
        "Доставка",
        "Создать адрес доставки",
        "Сохраняет новый адрес доставки для текущего пользователя.",
    ),
    ("PATCH", "/api/delivery/addresses/{address_id}"): OperationDoc(
        "Доставка",
        "Обновить адрес доставки",
        "Частично обновляет сохраненный адрес доставки текущего пользователя.",
    ),
    ("DELETE", "/api/delivery/addresses/{address_id}"): OperationDoc(
        "Доставка",
        "Удалить адрес доставки",
        "Удаляет адрес доставки текущего пользователя.",
    ),
    ("POST", "/api/delivery/webhooks/{provider_name}"): OperationDoc(
        "Доставка",
        "Принять вебхук доставки",
        "Обрабатывает подписанный вебхук службы доставки и обновляет отправление, трек-номер и статус доставки.",
    ),
    ("GET", "/api/notifications/messages"): OperationDoc(
        "Уведомления",
        "Получить сообщения уведомлений",
        "Административно возвращает сообщения уведомлений с фильтрами по статусу, каналу, шаблону и получателю.",
    ),
    ("POST", "/api/notifications/process"): OperationDoc(
        "Уведомления",
        "Обработать очередь уведомлений",
        "Административно запускает обработку очереди уведомлений ограниченным пакетом сообщений.",
    ),
    ("POST", "/api/chat"): OperationDoc(
        "Поддержка",
        "Отправить сообщение в чат поддержки",
        "Передает вопрос чат-боту поддержки. Для авторизованного пользователя бот может учитывать контекст последних заказов.",
    ),
    ("GET", "/api/support/tickets"): OperationDoc(
        "Поддержка",
        "Получить обращения поддержки",
        "Административный список обращений поддержки с фильтрами по статусу, приоритету, оператору, эскалации и поиску.",
    ),
    ("GET", "/api/support/tickets/admin/{ticket_id}"): OperationDoc(
        "Поддержка",
        "Получить обращение для администратора",
        "Административно возвращает обращение поддержки по UUID вместе с деталями диалога.",
    ),
    ("GET", "/api/support/tickets/me"): OperationDoc(
        "Поддержка",
        "Получить свои обращения поддержки",
        "Возвращает обращения поддержки текущего авторизованного пользователя.",
    ),
    ("GET", "/api/support/tickets/me/{ticket_id}"): OperationDoc(
        "Поддержка",
        "Получить свое обращение поддержки",
        "Возвращает конкретное обращение поддержки текущего пользователя.",
    ),
    ("POST", "/api/support/tickets/{ticket_id}/admin-reply"): OperationDoc(
        "Поддержка",
        "Ответить на обращение",
        "Добавляет ответ администратора или оператора в обращение поддержки и при необходимости меняет его статус.",
    ),
    ("PATCH", "/api/support/tickets/{ticket_id}"): OperationDoc(
        "Поддержка",
        "Обновить обращение поддержки",
        "Административно меняет статус, приоритет или назначенного оператора обращения поддержки.",
    ),
}

RESPONSE_DESCRIPTIONS = {
    "Successful Response": "Успешный ответ.",
    "Validation Error": "Ошибка валидации запроса.",
    "No Content": "Операция выполнена, тело ответа отсутствует.",
}


def install_custom_openapi(app: FastAPI) -> None:
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=API_TITLE,
            version=app.version,
            description=API_DESCRIPTION,
            routes=app.routes,
            tags=OPENAPI_TAGS,
        )
        _apply_operation_docs(schema)
        _translate_response_descriptions(schema)
        app.openapi_schema = _repair_mojibake(schema)
        return app.openapi_schema

    app.openapi = custom_openapi


def _apply_operation_docs(schema: dict[str, Any]) -> None:
    for path, methods in schema.get("paths", {}).items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if not isinstance(operation, dict):
                continue

            doc = OPERATION_DOCS.get((method.upper(), path))
            if not doc:
                continue

            operation["tags"] = [doc.tag]
            operation["summary"] = doc.summary
            operation["description"] = doc.description


def _translate_response_descriptions(schema: dict[str, Any]) -> None:
    for methods in schema.get("paths", {}).values():
        if not isinstance(methods, dict):
            continue
        for operation in methods.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses", {})
            if not isinstance(responses, dict):
                continue
            for response in responses.values():
                if not isinstance(response, dict):
                    continue
                description = response.get("description")
                if isinstance(description, str):
                    response["description"] = RESPONSE_DESCRIPTIONS.get(description, description)


def _repair_mojibake(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _repair_mojibake(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_repair_mojibake(item) for item in value]
    if isinstance(value, str):
        return _repair_string(value)
    return value


def _repair_string(value: str) -> str:
    try:
        fixed = value.encode("cp1251").decode("utf-8")
    except UnicodeError:
        return value

    return fixed if _mojibake_score(fixed) < _mojibake_score(value) else value


def _mojibake_score(value: str) -> int:
    markers = (
        "Р°",
        "Р±",
        "РІ",
        "Рі",
        "Рґ",
        "Рµ",
        "Р¶",
        "Р·",
        "Рё",
        "Р№",
        "Рє",
        "Р»",
        "Рј",
        "РЅ",
        "Рѕ",
        "Рї",
        "СЂ",
        "СЃ",
        "С‚",
        "Сѓ",
        "С„",
        "С…",
        "С†",
        "С‡",
        "С€",
        "С‰",
        "СЊ",
        "С‹",
        "СЌ",
        "СЋ",
        "СЏ",
        "Рђ",
        "Р‘",
        "Р’",
        "Р“",
        "Р”",
        "Р•",
        "Р–",
        "Р—",
        "Р",
        "Р™",
        "Рљ",
        "Р›",
        "Рњ",
        "Рќ",
        "Рћ",
        "Рџ",
        "РЎ",
        "Рў",
        "РЈ",
        "Р¤",
        "РҐ",
        "Р¦",
        "Р§",
        "РЁ",
        "Р©",
        "Р«",
        "Р¬",
        "Р­",
        "Р®",
        "РЇ",
        "В«",
        "В»",
    )
    return sum(value.count(marker) for marker in markers)
