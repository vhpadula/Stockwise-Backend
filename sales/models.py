import uuid
from django.db import models
from users.models import User
from inventory.models import Product


class SalesOrderManager(models.Manager):
    def for_user(self, user):
        if not user or not user.is_authenticated:
            return self.none()
        return self.filter(created_by=user)


class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("fulfilled", "Fulfilled"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    order_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = SalesOrderManager()

    @property
    def total_revenue(self):
        return sum(item.total_price for item in self.items.all())


class SalesOrderItemManager(models.Manager):
    def for_user(self, user):
        if not user or not user.is_authenticated:
            return self.none()
        return self.filter(created_by=user)


class SalesOrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="sales_items"
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = SalesOrderItemManager()
