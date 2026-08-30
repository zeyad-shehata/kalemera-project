import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Set
from fastapi import UploadFile, HTTPException, status

from app.config import settings, BACKEND_DIR
from app.services.image_service import image_service

class StorageService:
    """Storage Management Service.
    Handles file saving, directory partitioning (YYYY/MM), atomic replacement,
    safe deletion, orphan image detection, and storage usage calculations.
    """

    def __init__(self):
        self.storage_dir = Path(settings.STORAGE_DIR)
        self.products_dir = Path(settings.PRODUCTS_IMG_DIR)
        self.thumbnails_dir = Path(settings.THUMBNAILS_IMG_DIR)
        self.temp_dir = Path(settings.TEMP_DIR)
        self.backups_dir = Path(settings.BACKUPS_DIR)
        self.uploads_dir = Path(settings.UPLOAD_DIR)

        # Ensure core directories exist
        for directory in [self.storage_dir, self.products_dir, self.thumbnails_dir, self.temp_dir, self.backups_dir, self.uploads_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    async def save_product_image(self, file: UploadFile) -> Tuple[str, str, Dict[str, Any]]:
        """Validates incoming upload, processes through WebP optimization pipeline,
        and saves main image + thumbnail into partitioned storage.
        Returns: (main_relative_url, thumbnail_relative_url, metadata)
        """
        # Validate MIME type header first
        content_type = (file.content_type or "").lower()
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp", "image/heic"]
        if content_type and content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG, PNG, WebP, and HEIC images are allowed."
            )

        # Read file with size check
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.0f}MB."
            )

        # Process through ImageService (Pillow WebP pipeline)
        processed = image_service.process_image(contents)

        # Partition by Year/Month: e.g. 2026/08
        now = datetime.now(timezone.utc)
        year_month = now.strftime("%Y/%m")
        target_prod_dir = self.products_dir / year_month
        target_thumb_dir = self.thumbnails_dir / year_month
        target_prod_dir.mkdir(parents=True, exist_ok=True)
        target_thumb_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique UUID filename
        file_id = uuid.uuid4().hex
        main_filename = f"prod_{file_id}.webp"
        thumb_filename = f"thumb_{file_id}.webp"

        main_filepath = target_prod_dir / main_filename
        thumb_filepath = target_thumb_dir / thumb_filename

        # Write optimized WebP files to disk
        with open(main_filepath, "wb") as f:
            f.write(processed["main_bytes"])

        with open(thumb_filepath, "wb") as f:
            f.write(processed["thumb_bytes"])

        # Relative paths for web serving
        main_url = f"/storage/products/{year_month}/{main_filename}"
        thumb_url = f"/storage/thumbnails/{year_month}/{thumb_filename}"

        return main_url, thumb_url, processed

    def resolve_physical_path(self, relative_url: str) -> Optional[Path]:
        """Resolves a web relative URL into a verified absolute filesystem Path."""
        if not relative_url:
            return None

        clean_url = relative_url.lstrip("/")
        # If url is e.g. "storage/products/2026/08/prod_xxx.webp"
        if clean_url.startswith("storage/"):
            rel_part = clean_url.replace("storage/", "", 1)
            target = self.storage_dir / rel_part
        elif clean_url.startswith("uploads/"):
            rel_part = clean_url.replace("uploads/", "", 1)
            target = self.uploads_dir / rel_part
        else:
            target = BACKEND_DIR / clean_url

        if target.exists() and target.is_file():
            return target
        return None

    def delete_image(self, relative_url: Optional[str]) -> bool:
        """Safely removes an image and its potential thumbnail from disk."""
        if not relative_url:
            return False

        physical_path = self.resolve_physical_path(relative_url)
        if physical_path and physical_path.exists():
            try:
                os.remove(physical_path)
            except Exception:
                pass

        # Also attempt to delete corresponding thumbnail if it exists
        if "storage/products/" in relative_url:
            thumb_url = relative_url.replace("storage/products/", "storage/thumbnails/").replace("prod_", "thumb_")
            thumb_path = self.resolve_physical_path(thumb_url)
            if thumb_path and thumb_path.exists():
                try:
                    os.remove(thumb_path)
                except Exception:
                    pass

        return True

    async def replace_product_image(self, old_relative_url: Optional[str], new_file: UploadFile) -> Tuple[str, str, Dict[str, Any]]:
        """Atomic replacement: Saves new optimized image first, then unlinks old image."""
        main_url, thumb_url, meta = await self.save_product_image(new_file)
        
        # Only delete old image AFTER new one is successfully stored
        if old_relative_url and old_relative_url != main_url:
            self.delete_image(old_relative_url)

        return main_url, thumb_url, meta

    def get_storage_breakdown(self) -> Dict[str, Any]:
        """Calculates total disk storage consumption for images, database, backups, and OS disk free space."""
        def get_dir_size(path: Path) -> int:
            total = 0
            if not path.exists():
                return 0
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_dir_size(Path(entry.path))
            return total

        images_bytes = get_dir_size(self.products_dir) + get_dir_size(self.thumbnails_dir) + get_dir_size(self.uploads_dir)
        backups_bytes = get_dir_size(self.backups_dir)
        temp_bytes = get_dir_size(self.temp_dir)
        
        # Database size
        db_file = BACKEND_DIR / "kalemera.db"
        db_bytes = db_file.stat().st_size if db_file.exists() else 0

        total_app_bytes = images_bytes + backups_bytes + temp_bytes + db_bytes

        # OS Disk Free space
        try:
            total_disk, used_disk, free_disk = shutil.disk_usage(BACKEND_DIR)
        except Exception:
            total_disk, used_disk, free_disk = settings.HOSTING_STORAGE_LIMIT_BYTES, total_app_bytes, settings.HOSTING_STORAGE_LIMIT_BYTES - total_app_bytes

        hosting_limit = settings.HOSTING_STORAGE_LIMIT_BYTES
        usage_percent = round((total_app_bytes / hosting_limit) * 100, 2)

        return {
            "images_bytes": images_bytes,
            "images_mb": round(images_bytes / (1024 * 1024), 2),
            "database_bytes": db_bytes,
            "database_mb": round(db_bytes / (1024 * 1024), 2),
            "backups_bytes": backups_bytes,
            "backups_mb": round(backups_bytes / (1024 * 1024), 2),
            "temp_bytes": temp_bytes,
            "total_app_bytes": total_app_bytes,
            "total_app_mb": round(total_app_bytes / (1024 * 1024), 2),
            "disk_free_bytes": free_disk,
            "disk_free_gb": round(free_disk / (1024 * 1024 * 1024), 2),
            "hosting_limit_bytes": hosting_limit,
            "hosting_limit_gb": round(hosting_limit / (1024 * 1024 * 1024), 2),
            "usage_percent": usage_percent
        }

    def clean_orphan_images(self, active_image_urls: Set[str]) -> Dict[str, Any]:
        """Scans all stored images and safely deletes any files not present in active_image_urls."""
        cleaned_count = 0
        cleaned_bytes = 0

        # Normalize active paths for matching
        normalized_active = {url.strip().lstrip("/") for url in active_image_urls if url}

        # Check storage/products
        for root, _, files in os.walk(self.products_dir):
            for f in files:
                full_path = Path(root) / f
                # Construct relative url
                rel_url = str(full_path.relative_to(BACKEND_DIR)).replace("\\", "/").lstrip("/")
                if rel_url not in normalized_active and f"storage/{rel_url}" not in normalized_active:
                    size = full_path.stat().st_size
                    try:
                        os.remove(full_path)
                        cleaned_count += 1
                        cleaned_bytes += size
                    except Exception:
                        pass

        return {
            "cleaned_files": cleaned_count,
            "cleaned_bytes": cleaned_bytes,
            "cleaned_mb": round(cleaned_bytes / (1024 * 1024), 2)
        }

storage_service = StorageService()
