from rest_framework import viewsets, status, serializers
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

    def perform_update(self, serializer):
        order = self.get_object()
        if order.status != "draft":
            raise serializers.ValidationError("Only draft sales orders can be updated.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status != "draft":
            return Response(
                {"error": "Cannot delete sales orders that are not draft."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    # -------- Lifecycle Actions --------
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
    filterset_fields = ["sales_order"]

    def get_queryset(self):
        queryset = SalesOrderItem.objects.for_user(self.request.user).order_by(
            "-created_at"
        )
        sales_order_id = self.request.query_params.get("sales_order")
        if sales_order_id:
            queryset = queryset.filter(sales_order_id=sales_order_id)
        return queryset

    def perform_create(self, serializer):
        so_id = self.request.data.get("sales_order")
        so = SalesOrder.objects.for_user(self.request.user).get(id=so_id)
        if so.status != "draft":
            raise serializers.ValidationError(
                "Cannot add items to a non-draft sales order."
            )
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        soi = self.get_object()
        if soi.sales_order.status != "draft":
            raise serializers.ValidationError(
                "Cannot update items of a non-draft sales order."
            )
        serializer.save(
            total_price=serializer.validated_data["quantity"]
            * serializer.validated_data["unit_price"]
        )

    def destroy(self, request, *args, **kwargs):
        soi = self.get_object()
        if soi.sales_order.status != "draft":
            return Response(
                {"error": "Cannot delete items from a non-draft sales order."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)
