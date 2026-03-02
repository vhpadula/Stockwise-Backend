# inventory/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, StockViewSet

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"stocks", StockViewSet, basename="stock")

urlpatterns = [
    path("", include(router.urls)),
]
