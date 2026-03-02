from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalesOrderViewSet, SalesOrderItemViewSet

router = DefaultRouter()
router.register(r"orders", SalesOrderViewSet, basename="sales-order")
router.register(r"items", SalesOrderItemViewSet, basename="sales-order-item")

urlpatterns = [
    path("", include(router.urls)),
]
