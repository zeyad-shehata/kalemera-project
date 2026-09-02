import re
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models import UserRole, OrderStatus

# Egyptian mobile numbers: exactly 11 digits starting with 01 (e.g. 010, 011, 012, 015)
EGYPT_PHONE_REGEX = re.compile(r"^01[0-9]{9}$")


def validate_egypt_phone(v: str) -> str:
    if not v or not EGYPT_PHONE_REGEX.match(v.strip()):
        raise ValueError("Phone number must be an 11-digit Egyptian number (starts with 01).")
    return v.strip()


# User Schemas
class UserBase(BaseModel):
    phone: str
    full_name: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

    _validate_phone = field_validator("phone")(validate_egypt_phone)


class UserLogin(BaseModel):
    phone: str
    password: str = Field(..., min_length=1, max_length=100)

    _validate_phone = field_validator("phone")(validate_egypt_phone)


class UserResponse(UserBase):
    id: int
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Category Schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    product_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


# Product Schemas
class ProductVariantResponse(BaseModel):
    id: int
    product_id: int
    name: str
    price: float

    model_config = ConfigDict(from_attributes=True)

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    description_en: Optional[str] = Field(None, max_length=2000)
    price: float = Field(..., ge=0, le=1000000)
    stock: int = Field(..., ge=0, le=100000)
    category_id: int


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    image_path: Optional[str] = None
    created_at: datetime
    variants: List[ProductVariantResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Order Schemas
class OrderItemCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(..., gt=0, le=100)


ALLOWED_ADDRESSES = (
    "سكن الولاد الداخلي",
    "سكن البنات الداخلي",
    "الحي الراقي",
)

DELIVERY_FEES: dict[str, float] = {
    "سكن الولاد الداخلي": 20.0,
    "سكن البنات الداخلي": 15.0,
    "الحي الراقي": 25.0,
}


def calculate_delivery_fee(address: str | None) -> float:
    """Return the delivery fee for a validated address, or 0.0 for None/invalid."""
    if address and address in DELIVERY_FEES:
        return DELIVERY_FEES[address]
    return 0.0


class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1, max_length=50)
    delivery_address: Literal["سكن الولاد الداخلي", "سكن البنات الداخلي", "الحي الراقي"] = Field(..., description="Delivery address is required")


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name_snapshot: str
    product_name_en_snapshot: Optional[str] = None
    variant_id: Optional[int] = None
    variant_name_snapshot: Optional[str] = None
    price_snapshot: float
    quantity: int
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class OrderUserResponse(BaseModel):
    id: int
    phone: Optional[str] = None
    full_name: str

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    total_price: float
    delivery_address: Optional[str] = None
    delivery_fee: float = 0.0
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]
    user: Optional[OrderUserResponse] = None

    model_config = ConfigDict(from_attributes=True)



class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class AdminOrderWorkflow(BaseModel):
    """Admin orders grouped into workflow buckets (new/preparing/ready/delivered/cancelled)."""
    new: List[OrderResponse]
    preparing: List[OrderResponse]
    ready: List[OrderResponse]
    delivered: List[OrderResponse]
    cancelled: List[OrderResponse]
    delivered_total: int = 0


# Notification Schemas
class NotificationBase(BaseModel):
    message: str


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
