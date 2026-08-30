from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import User, UserRole

class UserRepository:
    async def get_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_phone(self, db: AsyncSession, phone: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.phone == phone))
        return result.scalars().first()

    async def create(
        self, db: AsyncSession, phone: str, hashed_password: str, full_name: str, role: UserRole = UserRole.CUSTOMER
    ) -> User:
        user = User(
            phone=phone,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

user_repository = UserRepository()
