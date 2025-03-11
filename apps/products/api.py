# apps/products/api.py
from ninja import Router, File
from ninja.files import UploadedFile
from ninja.pagination import paginate
from typing import List
from django.shortcuts import get_object_or_404
from .schemas import (
    CategorySchema, CategoryCreateSchema,
    ProductSchema, ProductCreateSchema, ProductUpdateSchema
)
from .models import Category, Product, ProductImage

router = Router()


# Category endpoints
@router.get("/categories", response=List[CategorySchema])
def list_categories(request):
    return Category.objects.filter(is_active=True)


@router.get("/categories/{category_id}", response=CategorySchema)
def get_category(request, category_id: int):
    return get_object_or_404(Category, id=category_id, is_active=True)


@router.post("/categories", response=CategorySchema)
def create_category(request, payload: CategoryCreateSchema):
    category_data = payload.dict()
    parent_id = category_data.pop('parent_id', None)

    if parent_id:
        parent = get_object_or_404(Category, id=parent_id)
        category = Category.objects.create(parent=parent, **category_data)
    else:
        category = Category.objects.create(**category_data)

    return category


# Product endpoints
@router.get("/products", response=List[ProductSchema])
@paginate
def list_products(request):
    return Product.objects.filter(is_active=True)


@router.get("/products/{product_id}", response=ProductSchema)
def get_product(request, product_id: int):
    return get_object_or_404(Product, id=product_id, is_active=True)


@router.post("/products", response=ProductSchema)
def create_product(request, payload: ProductCreateSchema):
    product_data = payload.dict()
    category_id = product_data.pop('category_id')
    category = get_object_or_404(Category, id=category_id)

    product = Product.objects.create(category=category, **product_data)
    return product


@router.put("/products/{product_id}", response=ProductSchema)
def update_product(request, product_id: int, payload: ProductUpdateSchema):
    product = get_object_or_404(Product, id=product_id)

    for attr, value in payload.dict(exclude_unset=True).items():
        if attr == 'category_id' and value is not None:
            category = get_object_or_404(Category, id=value)
            product.category = category
        else:
            setattr(product, attr, value)

    product.save()
    return product


@router.delete("/products/{product_id}", response={204: None})
def delete_product(request, product_id: int):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = False
    product.save()
    return 204, None


@router.post("/products/{product_id}/images", response=ProductSchema)
def upload_product_image(request, product_id: int, file: UploadedFile = File(...), is_primary: bool = False):
    product = get_object_or_404(Product, id=product_id)

    # If this is the primary image, set all other images to non-primary
    if is_primary:
        product.images.filter(is_primary=True).update(is_primary=False)

    # Create the new image
    ProductImage.objects.create(
        product=product,
        image=file,
        is_primary=is_primary
    )

    return product