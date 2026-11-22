from datetime import datetime
from typing import Optional
from decimal import Decimal
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from . import db

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name_bn: Mapped[str] = mapped_column(String(100), unique=True)
    products: Mapped[list["Product"]] = relationship(back_populates="category")

class Product(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name_bn: Mapped[str] = mapped_column(String(150), index=True)
    description_bn: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    base_unit: Mapped[str] = mapped_column(String(12)) # g, ml, piece
    price_per_base: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock_base: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    active: Mapped[bool] = mapped_column(default=True)
    category: Mapped[Category] = relationship(back_populates="products")
    __table_args__ = (CheckConstraint("stock_base >= 0", name="stock_nonnegative"),)

class Order(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="নতুন")
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    user: Mapped[User] = relationship(back_populates="orders")
    lines: Mapped[list["OrderLine"]] = relationship(back_populates="order", cascade="all, delete-orphan")

class OrderLine(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    product_name_bn: Mapped[str] = mapped_column(String(150))
    quantity_base: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit_label: Mapped[str] = mapped_column(String(20))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    order: Mapped[Order] = relationship(back_populates="lines")
