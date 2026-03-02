# inventory/serializers.py
from rest_framework import serializers
from .models import Product, Stock


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = [
            "id",
            "product",
            "purchase_order_item",
            "initial_quantity",
            "remaining_quantity",
            "unit_cost",
            "lot_number",
            "expiration_date",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    # Nested stocks, only include stocks created by the current user
    stocks = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "sku",
            "base_unit",
            "created_at",
            "updated_at",
            "stocks",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "stocks",
        ]  # prevent client from editing stocks

    def get_stocks(self, obj):
        """
        Return only the stocks belonging to the current user.
        """
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            # Use the Stock manager or filter manually
            user_stocks = obj.stocks.filter(created_by=user)
            return StockSerializer(user_stocks, many=True).data
        # fallback: empty list if no user
        return []
