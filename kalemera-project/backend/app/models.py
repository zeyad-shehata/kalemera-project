import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String,
    ForeignKey,
    Numeric,
    DateTime,
    Integer,
    Boolean,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="userrole_enum"),
        default=UserRole.CUSTOMER,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="category", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # Base price for non-variant products
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    variants: Mapped[List["ProductVariant"]] = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "S", "L"
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="variants")

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, name="orderstatus_enum"),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True
    )
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    product_name_en_snapshot: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    variant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    variant_name_snapshot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    price_snapshot: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")
    variant: Mapped[Optional["ProductVariant"]] = relationship("ProductVariant")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
