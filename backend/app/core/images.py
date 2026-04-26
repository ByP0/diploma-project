from app.core.config import setting


ALLOWED_IMAGE_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)

IMAGE_ROUTE_PREFIX = "/api/images"


def build_image_url(image_id: str) -> str:
    if setting.image_cdn_base_url:
        return f"{setting.image_cdn_base_url.rstrip('/')}/{image_id}"
    return f"{IMAGE_ROUTE_PREFIX}/{image_id}"


def build_image_urls(image_ids: list[str]) -> list[str]:
    return [build_image_url(image_id) for image_id in image_ids]
