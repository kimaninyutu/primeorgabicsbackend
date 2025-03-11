# apps/products/schemas.py
from ninja import Schema
from typing import List, Optional
from datetime import datetime

class CategorySchema(Schema):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    image: Optional[str] = None

class CategoryCreateSchema(Schema):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class ProductImageSchema(Schema):
    id: int
    image: str
    is_primary: bool

class ProductSchema(Schema):
    id: int
    name: str
    slug: str
    description: str
    price: float
    sale_price: Optional[float] = None
    category_id: int
    category_name: str
    stock: int
    is_active: bool
    is_featured: bool
    created_at: datetime
    images: List[ProductImageSchema] = []

class ProductCreateSchema(Schema):
    name: str
    description: str
    price: float
    sale_price: Optional[float] = None
    category_id: int
    stock: int = 0
    is_active: bool = True
    is_featured: bool = False

class ProductUpdateSchema(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    sale_price: Optional[float] = None
    category_id: Optional[int] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None