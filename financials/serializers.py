from rest_framework import serializers
from inventory.models import Product


class FinancialSummarySerializer(serializers.Serializer):
    total_purchased_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    total_purchase_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_sold_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    total_sales_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    profit_margin_percent = serializers.DecimalField(max_digits=5, decimal_places=2)


class ProductFinancialSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    quantity_sold = serializers.DecimalField(max_digits=12, decimal_places=3)
    sales_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    cogs = serializers.DecimalField(max_digits=12, decimal_places=2)
    profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    profit_margin_percent = serializers.DecimalField(max_digits=5, decimal_places=2)


class TimelineSerializer(serializers.Serializer):
    period = serializers.CharField()
    purchased_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    purchase_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    sold_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    sales_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    profit = serializers.DecimalField(max_digits=12, decimal_places=2)
