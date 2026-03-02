from rest_framework import serializers
from inventory.models import Stock
from .models import SalesOrder, SalesOrderItem


class SalesOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sales_order = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrder.objects.all(), required=False
    )

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
    items = SalesOrderItemSerializer(many=True)

    class Meta:
        model = SalesOrder
        fields = "__all__"
        read_only_fields = ["id", "created_by", "created_at", "total_revenue", "status"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        validated_data["created_by"] = self.context["request"].user
        order = SalesOrder.objects.create(**validated_data)
        for item_data in items_data:
            item_data["created_by"] = self.context["request"].user
            item_data["sales_order"] = order
            item_data["total_price"] = item_data["quantity"] * item_data["unit_price"]
            SalesOrderItem.objects.create(**item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        # Update order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            # Track existing items by id
            existing_items = {str(item.id): item for item in instance.items.all()}
            sent_item_ids = set()
            for item_data in items_data:
                item_id = str(item_data.get("id")) if item_data.get("id") else None
                if item_id and item_id in existing_items:
                    # Update existing item
                    item = existing_items[item_id]
                    for attr, value in item_data.items():
                        if attr != "id":
                            setattr(item, attr, value)
                    item.total_price = item.quantity * item.unit_price
                    item.save()
                    sent_item_ids.add(item_id)
                else:
                    # Create new item
                    item_data["created_by"] = self.context["request"].user
                    item_data["sales_order"] = instance
                    item_data["total_price"] = (
                        item_data["quantity"] * item_data["unit_price"]
                    )
                    SalesOrderItem.objects.create(**item_data)
            # Delete items not in sent list
            for item_id, item in existing_items.items():
                if item_id not in sent_item_ids:
                    item.delete()
        return instance
