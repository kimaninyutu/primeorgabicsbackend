# apps/wishlist/api.py
from ninja import Router

router = Router()

@router.get("/")
def get_wishlist(request):
    return {"message": "Wishlist API"}