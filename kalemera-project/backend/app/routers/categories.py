from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import CategoryResponse, CategoryCreate
from app.security import admin_required
from app.repositories.category_repository import category_repository

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("/", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    return await category_repository.list_with_counts(db)

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate,
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    existing = await category_repository.get_by_name(db, category_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists.",
        )
    return await category_repository.create(db, category_in.name)

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_in: CategoryCreate,
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    category = await category_repository.get_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return await category_repository.update(db, category, category_in.name)

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    category = await category_repository.get_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    if await category_repository.has_ordered_products(db, category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category cannot be deleted because some of its products are referenced in existing orders.",
        )

    await category_repository.delete(db, category)
    return None
