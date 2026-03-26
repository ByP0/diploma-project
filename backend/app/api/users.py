# app/api/v1/users.py
from fastapi import APIRouter, HTTPException, status
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead, UserUpdate
from app.api.deps import SessionDep, CurrentUser
from app.core.security import password_service

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: CurrentUser):
    return current_user

@router.put("/me", response_model=UserRead)
async def update_current_user(data: UserUpdate, session: SessionDep, current_user: CurrentUser):
    repo = UserRepository(session)
    if data.email:
        existing = await repo.get_by_email(data.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = data.email
    if data.password:
        password_service.validate(data.password)
        current_user.hashed_password = password_service.hash(data.password)
    await session.commit()
    await session.refresh(current_user)
    return current_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(session: SessionDep, current_user: CurrentUser):
    await session.delete(current_user)
    await session.commit()
    return {"detail": "User deleted"}
