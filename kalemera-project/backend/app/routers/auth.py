from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserResponse
from app.services.auth_service import auth_service
from app.security import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db, user_in)

@router.post("/login", response_model=UserResponse)
async def login(
    credentials: UserLogin, response: Response, db: AsyncSession = Depends(get_db)
):
    return await auth_service.authenticate_and_login(db, credentials, response)

@router.post("/logout")
async def logout(response: Response):
    return auth_service.logout(response)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
