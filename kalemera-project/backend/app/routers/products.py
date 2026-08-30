from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import ProductResponse
from app.security import admin_required
from app.repositories.product_repository import product_repository
from app.services.product_service import product_service

router = APIRouter(prefix="/api/products", tags=["products"])

def _parse_float(val) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, str) and not val.strip():
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

@router.get("/")
async def list_products(
    search: Optional[str] = None,
    category: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db),
):
    products, total = await product_repository.list_paginated(
        db=db,
        search=search,
        category=category,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )
    return {
        "items": [ProductResponse.model_validate(p) for p in products],
        "total": total,
        "page": page,
        "size": size,
    }

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await product_repository.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return product

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    name_en: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    description_en: Optional[str] = Form(None),
    price: float = Form(...),
    stock: int = Form(...),
    category_id: int = Form(...),
    price_s: Optional[str] = Form(None),
    price_l: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.create_product(
        db=db,
        name=name,
        name_en=name_en,
        description=description,
        description_en=description_en,
        price=price,
        stock=stock,
        category_id=category_id,
        price_s=_parse_float(price_s),
        price_l=_parse_float(price_l),
        image=image,
    )

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    name: str = Form(...),
    name_en: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    description_en: Optional[str] = Form(None),
    price: float = Form(...),
    stock: int = Form(...),
    category_id: int = Form(...),
    price_s: Optional[str] = Form(None),
    price_l: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    remove_image: bool = Form(False),
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.update_product(
        db=db,
        product_id=product_id,
        name=name,
        name_en=name_en,
        description=description,
        description_en=description_en,
        price=price,
        stock=stock,
        category_id=category_id,
        price_s=_parse_float(price_s),
        price_l=_parse_float(price_l),
        image=image,
        remove_image=remove_image,
    )

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    await product_service.delete_product(db, product_id)
    return None
