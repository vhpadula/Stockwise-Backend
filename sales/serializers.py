from rest_framework import serializers
from inventory.models import Stock
from .models import SalesOrder, SalesOrderItem


class SalesOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = "__all__"
        read_only_fields = ["id", "created_by", "created_at", "total_price"]

    def validate(self, attrs):
        quantity = attrs.get("quantity")
        unit_price = attrs.get("unit_price")
        if quantity <= 0 or unit_price <= 0:
            raise serializers.ValidationError(
                "Quantity and unit price must be positive."
            )
        return attrs

    def create(self, validated_data):
        validated_data["total_price"] = (
            validated_data["quantity"] * validated_data["unit_price"]
        )
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class SalesOrderSerializer(serializers.ModelSerializer):
    total_revenue = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    items = SalesOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = SalesOrder
        fields = "__all__"
        read_only_fields = ["id", "created_by", "created_at", "total_revenue", "status"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
