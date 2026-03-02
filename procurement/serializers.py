from rest_framework import serializers
from inventory.models import Stock
from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = "__all__"
        read_only_fields = ["id", "created_by", "created_at", "total_cost"]

    def validate(self, attrs):
        quantity = attrs.get("quantity")
        unit_cost = attrs.get("unit_cost")
        if quantity <= 0 or unit_cost <= 0:
            raise serializers.ValidationError(
                "Quantity and unit cost must be positive."
            )
        return attrs

    def create(self, validated_data):
        validated_data["total_cost"] = (
            validated_data["quantity"] * validated_data["unit_cost"]
        )
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class PurchaseOrderSerializer(serializers.ModelSerializer):
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = PurchaseOrder
        fields = "__all__"
        read_only_fields = ["id", "created_by", "created_at", "total_amount", "status"]
