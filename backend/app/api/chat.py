from fastapi import APIRouter, HTTPException

from app.api.docs import build_error_responses
from app.api.deps import OptionalCurrentUser, SessionDep
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService


router = APIRouter(prefix="/chat", tags=["Поддержка"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Отправить сообщение в чат поддержки",
    description="Передает вопрос в чат-бот поддержки. Для авторизованного пользователя бот учитывает контекст последних заказов.",
    responses=build_error_responses(400, 404, 422, 500),
)
async def support_chat(
    data: ChatRequest,
    session: SessionDep,
    current_user: OptionalCurrentUser,
):
    service = ChatService(session)
    try:
        result = await service.answer(
            message=data.message,
            user=current_user,
            ticket_id=data.ticket_id,
            contact_email=data.contact_email,
            request_human=data.request_human,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "не найдено" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc

    return ChatResponse(
        answer=result.answer,
        used_ai=result.used_ai,
        used_user_context=result.used_user_context,
        ticket_id=result.ticket.id,
        ticket_status=result.ticket.status,
        human_handoff_requested=result.ticket.human_handoff_requested,
    )
