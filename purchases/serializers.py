from rest_framework import serializers
from inventory.models import Stock
from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    purchase_order = serializers.PrimaryKeyRelatedField(
        queryset=PurchaseOrder.objects.all(), required=False
    )

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
    items = PurchaseOrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = "__all__"
        read_only_fields = ["id", "created_by", "created_at", "total_amount", "status"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        validated_data["created_by"] = self.context["request"].user
        order = PurchaseOrder.objects.create(**validated_data)
        for item_data in items_data:
            item_data["created_by"] = self.context["request"].user
            item_data["purchase_order"] = order
            item_data["total_cost"] = item_data["quantity"] * item_data["unit_cost"]
            PurchaseOrderItem.objects.create(**item_data)
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
                    item.total_cost = item.quantity * item.unit_cost
                    item.save()
                    sent_item_ids.add(item_id)
                else:
                    # Create new item
                    item_data["created_by"] = self.context["request"].user
                    item_data["purchase_order"] = instance
                    item_data["total_cost"] = (
                        item_data["quantity"] * item_data["unit_cost"]
                    )
                    PurchaseOrderItem.objects.create(**item_data)
            # Delete items not in sent list
            for item_id, item in existing_items.items():
                if item_id not in sent_item_ids:
                    item.delete()
        return instance
