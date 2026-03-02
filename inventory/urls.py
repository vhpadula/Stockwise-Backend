# inventory/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, StockMovementViewSet, StockViewSet

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"stocks", StockViewSet, basename="stock")
router.register(r"stock-movements", StockMovementViewSet, basename="stock-movement")

urlpatterns = [
    path("", include(router.urls)),
]
