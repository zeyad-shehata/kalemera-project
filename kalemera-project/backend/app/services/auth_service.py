from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from app.repositories.user_repository import user_repository
from app.schemas import UserCreate, UserLogin
from app.security import get_password_hash, verify_password, create_access_token

class AuthService:
    async def register_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        existing_user = await user_repository.get_by_phone(db, user_in.phone)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This phone number is already registered.",
            )

        hashed_password = get_password_hash(user_in.password)
        return await user_repository.create(
            db=db,
            phone=user_in.phone,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=UserRole.CUSTOMER,
        )

    async def authenticate_and_login(
        self, db: AsyncSession, credentials: UserLogin, response: Response
    ) -> User:
        user = await user_repository.get_by_phone(db, credentials.phone)
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect phone number or password.",
            )

        access_token = create_access_token(user_id=user.id, role=user.role.value)

        from app.config import settings
        is_secure = settings.SECURE_COOKIES or settings.is_production()

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=86400,  # 1 day
            samesite="lax",
            secure=is_secure,
            path="/",
        )

        return user

    def logout(self, response: Response) -> Dict[str, str]:
        response.delete_cookie(key="access_token", path="/")
        return {"message": "Successfully logged out"}

auth_service = AuthService()
