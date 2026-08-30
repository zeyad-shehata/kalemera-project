from typing import Optional, Dict, Any, List, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.repositories.product_repository import product_repository
from app.repositories.category_repository import category_repository
from app.services.storage_service import storage_service

class ProductService:
    def _validate_input(self, name: str, price: float, stock: int, has_variants: bool = False) -> None:
        if not name or not name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Product name is required."
            )
        try:
            price = float(price)
            stock = int(stock)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price and stock must be valid numbers.",
            )
        if price < 0 or (price == 0 and not has_variants):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be greater than zero.",
            )
        if stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Stock cannot be negative."
            )

    def _parse_names_and_desc(
        self, name: str, name_en: Optional[str], description: Optional[str], description_en: Optional[str]
    ) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
        parsed_ar = name.strip()
        parsed_en = (name_en or "").strip() or None

        if not parsed_en:
            if " - " in name:
                parts = name.split(" - ", 1)
                parsed_en = parts[0].strip()
                parsed_ar = parts[1].strip()
            else:
                parsed_en = name.strip()

        desc_ar = (description or "").strip() or None
        desc_en = (description_en or "").strip() or None
        if desc_ar and not desc_en:
            if " / " in desc_ar:
                parts = desc_ar.split(" / ", 1)
                desc_ar = parts[0].strip()
                desc_en = parts[1].strip()
            else:
                desc_en = desc_ar

        return parsed_ar, parsed_en, desc_ar, desc_en

    async def create_product(
        self,
        db: AsyncSession,
        name: str,
        name_en: Optional[str],
        description: Optional[str],
        description_en: Optional[str],
        price: float,
        stock: int,
        category_id: int,
        price_s: Optional[float] = None,
        price_l: Optional[float] = None,
        image: Optional[UploadFile] = None,
    ) -> Product:
        has_variants = price_s is not None or price_l is not None
        self._validate_input(name, price, stock, has_variants=has_variants)

        category = await category_repository.get_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specified category does not exist.",
            )

        image_path = None
        if image and image.filename:
            image_path, _, _ = await storage_service.save_product_image(image)

        name_ar, name_en, desc_ar, desc_en = self._parse_names_and_desc(name, name_en, description, description_en)

        return await product_repository.create(
            db=db,
            name=name_ar,
            name_en=name_en,
            description=desc_ar,
            description_en=desc_en,
            price=price,
            stock=stock,
            category_id=category_id,
            image_path=image_path,
            price_s=price_s,
            price_l=price_l,
        )

    async def update_product(
        self,
        db: AsyncSession,
        product_id: int,
        name: str,
        name_en: Optional[str],
        description: Optional[str],
        description_en: Optional[str],
        price: float,
        stock: int,
        category_id: int,
        price_s: Optional[float] = None,
        price_l: Optional[float] = None,
        image: Optional[UploadFile] = None,
        remove_image: bool = False,
    ) -> Product:
        has_variants = price_s is not None or price_l is not None
        self._validate_input(name, price, stock, has_variants=has_variants)

        product = await product_repository.get_by_id(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        category = await category_repository.get_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specified category does not exist.",
            )

        image_path = product.image_path
        if image and image.filename:
            image_path, _, _ = await storage_service.replace_product_image(product.image_path, image)
        elif remove_image:
            if product.image_path:
                storage_service.delete_image(product.image_path)
            image_path = None

        name_ar, name_en, desc_ar, desc_en = self._parse_names_and_desc(name, name_en, description, description_en)

        return await product_repository.update(
            db=db,
            product=product,
            name=name_ar,
            name_en=name_en,
            description=desc_ar,
            description_en=desc_en,
            price=price,
            stock=stock,
            category_id=category_id,
            image_path=image_path,
            price_s=price_s,
            price_l=price_l,
        )

    async def delete_product(self, db: AsyncSession, product_id: int) -> None:
        product = await product_repository.get_by_id(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        if await product_repository.is_referenced_in_orders(db, product_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product cannot be deleted because it is referenced in existing orders.",
            )

        if product.image_path:
            storage_service.delete_image(product.image_path)

        await product_repository.delete(db, product)

product_service = ProductService()
