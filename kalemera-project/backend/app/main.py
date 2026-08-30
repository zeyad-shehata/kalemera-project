import os
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, products, categories, orders, notifications, reports, storage

app = FastAPI(
    title="Kalemera Project API",
    description="Backend API for Kalemera E-commerce application",
    version="1.0.0",
)

# Enable GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production():
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Rate Limiting Middleware
from app.middleware.rate_limiter import RateLimiterMiddleware
app.add_middleware(RateLimiterMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_origin_regex=r"^https?:\/\/(localhost|127\.0\.0\.1|.*\.vercel\.app)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global safe exception handler
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("kalmera.api")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

# Ensure upload and storage directories exist safely
for dir_path in [settings.UPLOAD_DIR, settings.PRODUCTS_IMG_DIR, settings.THUMBNAILS_IMG_DIR, settings.TEMP_DIR, settings.BACKUPS_DIR]:
    try:
        os.makedirs(dir_path, exist_ok=True)
    except OSError:
        pass

# Mount ONLY public product images and thumbnails statically
# (Isolates backups, temp files, and database files from HTTP static access)
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
if os.path.exists(settings.PRODUCTS_IMG_DIR):
    app.mount("/storage/products", StaticFiles(directory=settings.PRODUCTS_IMG_DIR), name="products_storage")
if os.path.exists(settings.THUMBNAILS_IMG_DIR):
    app.mount("/storage/thumbnails", StaticFiles(directory=settings.THUMBNAILS_IMG_DIR), name="thumbnails_storage")


# Register routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(orders.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(storage.router)


@app.get("/", tags=["root"])
@app.get("/api", tags=["root"])
@app.get("/api/", tags=["root"])
async def root():
    return {
        "message": "Welcome to Kalemera Project API",
        "documentation": "/docs",
        "health_check": "/api/health",
    }


@app.get("/health", status_code=status.HTTP_200_OK, tags=["health"])
@app.get("/api/health", status_code=status.HTTP_200_OK, tags=["health"])
async def health_check():
    return {"status": "healthy"}

