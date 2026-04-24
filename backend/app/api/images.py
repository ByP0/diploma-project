from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Path, Request, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentAdmin, SessionDep
from app.api.docs import build_error_responses, message_response
from app.schemas.common import MessageResponse
from app.schemas.image import ImageUploadResponse
from app.services.admin_audit_service import AdminAuditService
from app.services.image_service import ImageNotFoundError, ImageService, ImageValidationError


router = APIRouter(prefix="/images", tags=["Медиа"])


@router.post(
    "",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить изображение",
    responses=build_error_responses(401, 403, 413, 415, 422, 500),
)
async def upload_image(
    file: Annotated[UploadFile, File(description="Файл изображения")],
    request: Request,
    session: SessionDep,
    current_admin: CurrentAdmin,
):
    service = ImageService()
    try:
        image = await service.upload(file)
    except ImageValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    await AdminAuditService(session).record(
        request=request,
        admin_user=current_admin,
        action="upload",
        resource_type="image",
        resource_id=image.id,
        status_code=201,
        details={"filename": image.filename, "content_type": image.content_type},
    )
    return ImageUploadResponse(
        id=image.id,
        url=image.url,
        filename=image.filename,
        content_type=image.content_type,
        size_bytes=image.size_bytes,
    )


@router.get(
    "/{image_id}",
    summary="Получить изображение",
    responses={
        **build_error_responses(404, 500),
        200: {
            "description": "Бинарное содержимое изображения.",
            "content": {
                "image/jpeg": {},
                "image/png": {},
                "image/webp": {},
                "image/gif": {},
            },
        },
    },
)
async def get_image(
    image_id: Annotated[str, Path()],
):
    service = ImageService()
    try:
        grid_out = await service.open_download_stream(image_id)
    except ImageNotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return StreamingResponse(
        service.iter_file(grid_out),
        media_type=service.get_media_type(grid_out),
        headers=service.build_download_headers(grid_out, image_id),
    )


@router.delete(
    "/{image_id}",
    response_model=MessageResponse,
    summary="Удалить изображение",
    responses={
        **build_error_responses(401, 403, 404, 422, 500),
        200: message_response("Изображение успешно удалено."),
    },
)
async def delete_image(
    image_id: Annotated[str, Path()],
    request: Request,
    session: SessionDep,
    current_admin: CurrentAdmin,
):
    service = ImageService()
    try:
        await service.delete(image_id)
    except ImageNotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    await AdminAuditService(session).record(
        request=request,
        admin_user=current_admin,
        action="delete",
        resource_type="image",
        resource_id=image_id,
        status_code=200,
    )
    return MessageResponse(detail="Изображение успешно удалено.")
