from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import SalesOrder, SalesOrderItem
from .serializers import SalesOrderSerializer, SalesOrderItemSerializer
from inventory.models import Stock
from inventory.models import StockMovement
from django.db import transaction, models


class SalesOrderViewSet(viewsets.ModelViewSet):
    serializer_class = SalesOrderSerializer

    def get_queryset(self):
        return SalesOrder.objects.for_user(self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        order = self.get_object()
        if order.status != "draft":
            return Response(
                {"error": "Only draft orders can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = "confirmed"
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status not in ["draft", "confirmed"]:
            return Response(
                {"error": "Only draft or confirmed orders can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = "cancelled"
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def fulfill(self, request, pk=None):
        order = self.get_object()

        if order.status != "confirmed":
            return Response(
                {"error": "Only confirmed orders can be fulfilled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for item in order.items.all():
            remaining_qty = item.quantity
            stocks = Stock.objects.filter(
                product=item.product, remaining_quantity__gt=0
            ).order_by(
                "created_at"
            )  # FIFO

            total_available = (
                stocks.aggregate(total=models.Sum("remaining_quantity"))["total"] or 0
            )
            if total_available < remaining_qty:
                return Response(
                    {"error": f"Insufficient stock for product {item.product.name}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for stock in stocks:
                consume_qty = min(stock.remaining_quantity, remaining_qty)
                stock.remaining_quantity -= consume_qty
                stock.save()

                StockMovement.objects.create(
                    stock=stock,
                    sales_order_item=item,
                    quantity=consume_qty,
                    cost_per_unit=stock.unit_cost,
                    created_by=request.user,
                )

                remaining_qty -= consume_qty
                if remaining_qty <= 0:
                    break

        order.status = "fulfilled"
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)


class SalesOrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = SalesOrderItemSerializer

    def get_queryset(self):
        return SalesOrderItem.objects.for_user(self.request.user).order_by(
            "-created_at"
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
