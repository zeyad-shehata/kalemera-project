import io
import os
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageOps
from fastapi import HTTPException, status
from app.config import settings

# Set Pillow maximum image pixels to protect against Decompression Bomb DOS attacks
Image.MAX_IMAGE_PIXELS = 25000000  # 25 Megapixels limit
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP", "GIF"}

class ImageService:
    """High-performance image processing pipeline with Pillow.
    Optimizes photos to WebP format, strips EXIF, resizes to max dimensions,
    and produces high quality images with low storage consumption.
    """

    def __init__(self):
        self.max_width = settings.IMAGE_MAX_WIDTH
        self.max_height = settings.IMAGE_MAX_HEIGHT
        self.quality = settings.IMAGE_QUALITY
        self.thumb_width = settings.THUMBNAIL_MAX_WIDTH
        self.thumb_height = settings.THUMBNAIL_MAX_HEIGHT

    def process_image(self, file_bytes: bytes) -> Dict[str, Any]:
        """Validates, strips EXIF, resizes, and converts input image to WebP.
        Also generates a companion 400px thumbnail.
        """
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE / (1024*1024):.1f}MB."
            )

        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Validate format
            if image.format not in ALLOWED_FORMATS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported image format: {image.format}. Allowed: {', '.join(ALLOWED_FORMATS)}"
                )
            # Validate image integrity
            image.verify()
            # Re-open for actual processing (verify() corrupts internal state for further operations)
            image = Image.open(io.BytesIO(file_bytes))
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or corrupted image file."
            )

        orig_w, orig_h = image.size
        if orig_w > 10000 or orig_h > 10000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image dimensions exceed maximum allowable bounds."
            )

        # 1. Correct orientation using EXIF if present (e.g. mobile camera rotation)
        try:
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass

        # 2. Convert mode to RGB or RGBA (dropping CMYK, palette, etc.)
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            # Keep transparency channel for PNG/WebP with alpha
            image = image.convert("RGBA")
        else:
            image = image.convert("RGB")

        orig_w, orig_h = image.size

        # 3. Resize main image if larger than max dimensions (preserve aspect ratio)
        main_img = image.copy()
        if orig_w > self.max_width or orig_h > self.max_height:
            main_img.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)

        main_w, main_h = main_img.size

        # 4. Encode Main Image to WebP (strip EXIF metadata automatically)
        main_output = io.BytesIO()
        main_img.save(
            main_output,
            format="WEBP",
            quality=self.quality,
            method=6,  # Slower encoding but produces smallest size
            optimize=True
        )
        main_webp_bytes = main_output.getvalue()

        # 5. Generate Thumbnail (max 400x400)
        thumb_img = image.copy()
        thumb_img.thumbnail((self.thumb_width, self.thumb_height), Image.Resampling.LANCZOS)
        thumb_w, thumb_h = thumb_img.size

        thumb_output = io.BytesIO()
        thumb_img.save(
            thumb_output,
            format="WEBP",
            quality=75,
            method=6,
            optimize=True
        )
        thumb_webp_bytes = thumb_output.getvalue()

        return {
            "main_bytes": main_webp_bytes,
            "main_size": len(main_webp_bytes),
            "main_width": main_w,
            "main_height": main_h,
            "thumb_bytes": thumb_webp_bytes,
            "thumb_size": len(thumb_webp_bytes),
            "thumb_width": thumb_w,
            "thumb_height": thumb_h,
            "original_width": orig_w,
            "original_height": orig_h,
            "original_size": len(file_bytes),
            "mime_type": "image/webp"
        }

image_service = ImageService()
