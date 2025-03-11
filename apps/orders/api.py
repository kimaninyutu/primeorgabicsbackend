# apps/orders/api.py
from ninja import Router

router = Router()

@router.get("/")
def list_orders(request):
    return {"message": "Orders API"}