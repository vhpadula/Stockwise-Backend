import uuid
from django.db import models
from users.models import User


class Product(models.Model):
    UNIT_CHOICES = [
        ("g", "Gram"),
        ("kg", "Kilogram"),
        ("ml", "Milliliter"),
        ("L", "Liter"),
        ("unit", "Unit"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    sku = models.CharField(max_length=100, unique=True)
    base_unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Stock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="stocks"
    )
    purchase_order_item = models.ForeignKey(
        "procurement.PurchaseOrderItem",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    initial_quantity = models.DecimalField(max_digits=12, decimal_places=3)
    remaining_quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    lot_number = models.CharField(max_length=100, null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class StockMovement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="movements")
    sales_order_item = models.ForeignKey(
        "sales.SalesOrderItem", null=True, blank=True, on_delete=models.SET_NULL
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
