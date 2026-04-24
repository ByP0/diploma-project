from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.docs import build_error_responses
from app.core.cookies import clear_auth_cookies, set_access_cookie, set_refresh_cookie
from app.core.config import setting
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.schemas.token import TokenPair
from app.services.auth_service import AuthService, AuthError
from app.api.deps import SessionDep

router = APIRouter(prefix="/auth", tags=["Аутентификация"])

@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать пользователя",
    description="Создает нового покупателя интернет-магазина по адресу электронной почты и паролю.",
    responses=build_error_responses(400, 422, 500),
)
async def register(
    data: UserCreate,
    session: SessionDep,
):
    service = AuthService(session)

    try:
        user = await service.register(data.email, data.password)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return user

@router.post(
    "/login",
    response_model=UserRead,
    summary="Войти в систему",
    description="Проверяет учетные данные пользователя и сохраняет токены доступа и обновления в браузере с защитой от доступа клиентских скриптов.",
    responses=build_error_responses(401, 422, 500),
)
async def login(
    data: UserLogin,
    response: Response,
    session: SessionDep,
):
    service = AuthService(session)

    try:
        user = await service.login(data.email, data.password, response)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    return user

@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Обновить токены доступа",
    description="Создает новую пару токенов на основе токена обновления, сохраненного в браузере.",
    responses=build_error_responses(401, 500),
)
async def refresh(
    response: Response,
    request: Request,
    session: SessionDep,
):
    refresh_token = request.cookies.get(setting.refresh_cookie_name)

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Токен обновления не найден в браузере.")

    service = AuthService(session)

    try:
        new_access, new_refresh = await service.refresh(refresh_token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    set_access_cookie(response, new_access)
    set_refresh_cookie(response, new_refresh)

    return TokenPair(
        access_token=new_access,
        refresh_token=new_refresh,
    )

@router.post(
    "/logout",
    status_code=204,
    summary="Выйти из системы",
    description="Удаляет из браузера токены доступа и обновления и отзывает токен обновления, если он был передан.",
    responses=build_error_responses(500),
)
async def logout(
    response: Response,
    request: Request,
    session: SessionDep,
):
    refresh_token = request.cookies.get(setting.refresh_cookie_name)

    service = AuthService(session)

    if refresh_token:
        await service.logout(refresh_token)

    clear_auth_cookies(response)
