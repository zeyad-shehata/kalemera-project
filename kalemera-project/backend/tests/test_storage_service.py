import pytest
import io
from PIL import Image
from fastapi import UploadFile
from app.services.image_service import image_service
from app.services.storage_service import storage_service

def test_image_optimization_and_webp_conversion():
    # Create a dummy large RGBA image (2000x2000)
    raw_img = Image.new("RGBA", (2000, 2000), color=(212, 155, 84, 255))
    output_bytes = io.BytesIO()
    raw_img.save(output_bytes, format="PNG")
    png_bytes = output_bytes.getvalue()

    # Process through image service
    processed = image_service.process_image(png_bytes)

    assert processed["mime_type"] == "image/webp"
    # Verify dimensions are clamped to max 1200
    assert processed["main_width"] <= 1200
    assert processed["main_height"] <= 1200
    assert processed["thumb_width"] <= 400
    assert processed["thumb_height"] <= 400

    # Verify WebP header
    assert processed["main_bytes"][:4] == b"RIFF"
    assert b"WEBP" in processed["main_bytes"][:16]

    # Verify substantial compression (WebP should be significantly smaller than raw PNG)
    assert processed["main_size"] < len(png_bytes)


def test_storage_breakdown():
    breakdown = storage_service.get_storage_breakdown()
    assert "images_bytes" in breakdown
    assert "database_bytes" in breakdown
    assert "backups_bytes" in breakdown
    assert "total_app_mb" in breakdown
    assert "disk_free_gb" in breakdown
    assert "usage_percent" in breakdown
    assert breakdown["hosting_limit_gb"] == 10
