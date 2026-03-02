from rest_framework.routers import DefaultRouter
from .views import PurchaseOrderViewSet, PurchaseOrderItemViewSet

router = DefaultRouter()
router.register(r"orders", PurchaseOrderViewSet, basename="purchase-order")
router.register(r"items", PurchaseOrderItemViewSet, basename="purchase-order-item")

urlpatterns = router.urls
