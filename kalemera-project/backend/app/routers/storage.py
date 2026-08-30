from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.security import admin_required
from app.services.storage_service import storage_service
from app.services.backup_service import backup_service
from app.repositories.product_repository import product_repository

router = APIRouter(prefix="/api/storage", tags=["storage"])

@router.get("/overview")
async def get_storage_overview(admin_user=Depends(admin_required)) -> Dict[str, Any]:
    """Returns disk usage and storage metrics to track the 5 GB hosting limit."""
    return storage_service.get_storage_breakdown()

@router.get("/backups")
async def list_backups(admin_user=Depends(admin_required)) -> List[Dict[str, Any]]:
    """Lists all stored database backups."""
    return backup_service.list_backups()

@router.post("/backup")
async def trigger_manual_backup(admin_user=Depends(admin_required)) -> Dict[str, Any]:
    """Triggers an atomic database backup and enforces rolling 7-backup retention."""
    return backup_service.create_backup()

@router.post("/clean-orphans")
async def clean_orphaned_images(
    admin_user=Depends(admin_required), db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Scans and removes any unreferenced images to reclaim storage space."""
    active_paths = set(await product_repository.get_all_active_image_paths(db))
    return storage_service.clean_orphan_images(active_paths)
