# core/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI
from ninja import Router
from django.http import HttpResponse

# Import your routers
from apps.accounts.api import router as accounts_router
from apps.products.api import router as products_router
from apps.orders.api import router as orders_router
from apps.cart.api import router as cart_router
from apps.payments.api import router as payments_router
from apps.wishlist.api import router as wishlist_router

# Initialize the API
api = NinjaAPI()

# Add routers
api.add_router("/auth/", accounts_router)
api.add_router("/products/", products_router)
api.add_router("/orders/", orders_router)
api.add_router("/cart/", cart_router)
api.add_router("/payments/", payments_router)
api.add_router("/wishlist/", wishlist_router)

health_router = Router()

@health_router.get("/")
def health_check(request):
    """Health check endpoint for Render"""
    return HttpResponse("OK")

# Then in your main API router:
api.add_router("/health", health_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)