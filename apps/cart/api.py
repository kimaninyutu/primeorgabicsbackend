# apps/cart/api.py
from ninja import Router

router = Router()

@router.get("/")
def get_cart(request):
    return {"message": "Cart API"}