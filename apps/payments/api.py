# apps/payments/api.py
from ninja import Router

router = Router()

@router.get("/")
def list_payments(request):
    return {"message": "Payments API"}