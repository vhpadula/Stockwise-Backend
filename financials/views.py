from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, F
from inventory.models import Product, StockMovement, Stock
from sales.models import SalesOrderItem
from purchases.models import PurchaseOrderItem
from .serializers import (
    FinancialSummarySerializer,
    ProductFinancialSerializer,
    TimelineSerializer,
)
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from decimal import Decimal
from datetime import datetime


def parse_date(param):
    try:
        return datetime.strptime(param, "%Y-%m-%d").date()
    except Exception:
        return None


class FinancialSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from = parse_date(request.query_params.get("date_from"))
        date_to = parse_date(request.query_params.get("date_to"))

        purchase_qs = PurchaseOrderItem.objects.filter(created_by=request.user)
        sales_qs = SalesOrderItem.objects.filter(created_by=request.user)

        if date_from:
            purchase_qs = purchase_qs.filter(created_at__date__gte=date_from)
            sales_qs = sales_qs.filter(created_at__date__gte=date_from)
        if date_to:
            purchase_qs = purchase_qs.filter(created_at__date__lte=date_to)
            sales_qs = sales_qs.filter(created_at__date__lte=date_to)

        total_purchased_quantity = (
            purchase_qs.aggregate(total=Sum("quantity"))["total"] or 0
        )
        total_purchase_value = (
            purchase_qs.aggregate(total=Sum("total_cost"))["total"] or 0
        )
        total_sold_quantity = sales_qs.aggregate(total=Sum("quantity"))["total"] or 0
        total_sales_value = sales_qs.aggregate(total=Sum("total_price"))["total"] or 0
        total_profit = Decimal(total_sales_value) - Decimal(total_purchase_value)
        profit_margin_percent = (
            (total_profit / total_sales_value * 100) if total_sales_value else 0
        )

        data = {
            "total_purchased_quantity": total_purchased_quantity,
            "total_purchase_value": total_purchase_value,
            "total_sold_quantity": total_sold_quantity,
            "total_sales_value": total_sales_value,
            "total_profit": total_profit,
            "profit_margin_percent": round(profit_margin_percent, 2),
        }

        serializer = FinancialSummarySerializer(data)
        return Response(serializer.data)


class ProductFinancialView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from = parse_date(request.query_params.get("date_from"))
        date_to = parse_date(request.query_params.get("date_to"))
        product_filter = request.query_params.get("product")

        sales_qs = SalesOrderItem.objects.filter(created_by=request.user)
        if date_from:
            sales_qs = sales_qs.filter(created_at__date__gte=date_from)
        if date_to:
            sales_qs = sales_qs.filter(created_at__date__lte=date_to)
        if product_filter:
            sales_qs = sales_qs.filter(product_id=product_filter)

        data = []
        for product in Product.objects.filter(
            stocks__created_by=request.user
        ).distinct():
            prod_sales = sales_qs.filter(product=product)
            quantity_sold = prod_sales.aggregate(total=Sum("quantity"))["total"] or 0
            sales_revenue = prod_sales.aggregate(total=Sum("total_price"))["total"] or 0

            # COGS using StockMovements
            stock_movements = StockMovement.objects.filter(
                stock__product=product, created_by=request.user
            )
            if date_from:
                stock_movements = stock_movements.filter(
                    created_at__date__gte=date_from
                )
            if date_to:
                stock_movements = stock_movements.filter(created_at__date__lte=date_to)

            cogs = (
                stock_movements.aggregate(
                    total=Sum(F("quantity") * F("cost_per_unit"))
                )["total"]
                or 0
            )
            profit = Decimal(sales_revenue) - Decimal(cogs)
            profit_margin_percent = (
                (profit / sales_revenue * 100) if sales_revenue else 0
            )

            data.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity_sold": quantity_sold,
                    "sales_revenue": sales_revenue,
                    "cogs": cogs,
                    "profit": profit,
                    "profit_margin_percent": round(profit_margin_percent, 2),
                }
            )

        serializer = ProductFinancialSerializer(data, many=True)
        return Response(serializer.data)


class TimelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        group_by = request.query_params.get("group_by", "day")
        date_from = parse_date(request.query_params.get("date_from"))
        date_to = parse_date(request.query_params.get("date_to"))
        product_id = request.query_params.get("product")

        trunc_map = {"day": TruncDay, "week": TruncWeek, "month": TruncMonth}
        trunc_func = trunc_map.get(group_by, TruncDay)

        # Purchases
        purchase_qs = PurchaseOrderItem.objects.filter(created_by=request.user)
        if product_id:
            purchase_qs = purchase_qs.filter(product_id=product_id)
        if date_from:
            purchase_qs = purchase_qs.filter(created_at__date__gte=date_from)
        if date_to:
            purchase_qs = purchase_qs.filter(created_at__date__lte=date_to)

        purchase_qs = (
            purchase_qs.annotate(period=trunc_func("created_at"))
            .values("period")
            .annotate(
                purchased_quantity=Sum("quantity"),
                purchase_value=Sum("total_cost"),
            )
        )

        # Sales
        sales_qs = SalesOrderItem.objects.filter(created_by=request.user)
        if product_id:
            sales_qs = sales_qs.filter(product_id=product_id)
        if date_from:
            sales_qs = sales_qs.filter(created_at__date__gte=date_from)
        if date_to:
            sales_qs = sales_qs.filter(created_at__date__lte=date_to)

        sales_qs = (
            sales_qs.annotate(period=trunc_func("created_at"))
            .values("period")
            .annotate(
                sold_quantity=Sum("quantity"),
                sales_value=Sum("total_price"),
            )
        )

        # Merge data by period
        timeline = {}
        for p in purchase_qs:
            key = p["period"].strftime("%Y-%m-%d")
            timeline[key] = {
                "period": key,
                "purchased_quantity": p["purchased_quantity"],
                "purchase_value": p["purchase_value"],
                "sold_quantity": 0,
                "sales_value": 0,
                "profit": 0,
            }

        for s in sales_qs:
            key = s["period"].strftime("%Y-%m-%d")
            if key not in timeline:
                timeline[key] = {
                    "period": key,
                    "purchased_quantity": 0,
                    "purchase_value": 0,
                    "sold_quantity": 0,
                    "sales_value": 0,
                    "profit": 0,
                }
            timeline[key]["sold_quantity"] = s["sold_quantity"]
            timeline[key]["sales_value"] = s["sales_value"]
            timeline[key]["profit"] = s["sales_value"] - timeline[key]["purchase_value"]

        serializer = TimelineSerializer(list(timeline.values()), many=True)
        return Response(serializer.data)


class TopProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get("limit", 5))
        date_from = parse_date(request.query_params.get("date_from"))
        date_to = parse_date(request.query_params.get("date_to"))

        sales_qs = SalesOrderItem.objects.filter(created_by=request.user)
        if date_from:
            sales_qs = sales_qs.filter(created_at__date__gte=date_from)
        if date_to:
            sales_qs = sales_qs.filter(created_at__date__lte=date_to)

        products_profit = {}
        for sale in sales_qs:
            stock_movements = StockMovement.objects.filter(
                stock__product=sale.product, created_by=request.user
            )
            if date_from:
                stock_movements = stock_movements.filter(
                    created_at__date__gte=date_from
                )
            if date_to:
                stock_movements = stock_movements.filter(created_at__date__lte=date_to)
            cogs = (
                stock_movements.aggregate(
                    total=Sum(F("quantity") * F("cost_per_unit"))
                )["total"]
                or 0
            )
            profit = Decimal(sale.total_price) - Decimal(cogs)
            if sale.product.id not in products_profit:
                products_profit[sale.product.id] = {
                    "product_name": sale.product.name,
                    "profit": profit,
                }
            else:
                products_profit[sale.product.id]["profit"] += profit

        top_products = sorted(
            products_profit.items(), key=lambda x: x[1]["profit"], reverse=True
        )[:limit]
        return Response(
            [
                {
                    "product_id": pid,
                    "product_name": data["product_name"],
                    "profit": round(data["profit"], 2),
                }
                for pid, data in top_products
            ]
        )
