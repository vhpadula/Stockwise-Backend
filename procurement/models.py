import uuid
from django.db import models
from users.models import User
from inventory.models import Product


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("received", "Received"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    order_date = models.DateField()
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="purchase_orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_amount(self):
        return sum(item.total_cost for item in self.items.all())


class PurchaseOrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="purchase_items"
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
