from django.db import transaction
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from inventory.models import Stock
from inventory.serializers import StockSerializer
from .models import PurchaseOrder, PurchaseOrderItem
from .serializers import PurchaseOrderSerializer, PurchaseOrderItemSerializer


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer

    def get_queryset(self):
        return PurchaseOrder.objects.for_user(self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        po = self.get_object()
        if po.status != "draft":
            raise serializers.ValidationError(
                "Only draft purchase orders can be updated."
            )
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        po = self.get_object()
        if po.status != "draft":
            return Response(
                {"error": "Cannot delete purchase orders that are not draft."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    # -------- Lifecycle Actions --------
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        po = self.get_object()
        if po.status != "draft":
            return Response(
                {"error": "Only draft purchase orders can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        po.status = "confirmed"
        po.save(update_fields=["status"])
        return Response({"status": "confirmed"})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        po = self.get_object()
        if po.status == "received":
            return Response(
                {"error": "Cannot cancel a received purchase order."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        po.status = "cancelled"
        po.save(update_fields=["status"])
        return Response({"status": "cancelled"})

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        po = self.get_object()
        if po.status != "confirmed":
            return Response(
                {"error": "Only confirmed purchase orders can be received."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = po.items.all()
        if not items.exists():
            return Response(
                {"error": "Cannot receive a purchase order with no items."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for item in items:
                Stock.objects.create(
                    product=item.product,
                    purchase_order_item=item,
                    initial_quantity=item.quantity,
                    remaining_quantity=item.quantity,
                    unit_cost=item.unit_cost,
                    lot_number=item.lot_number or f"LOT-{item.id.hex[:6]}",
                    expiration_date=item.expiration_date,
                    created_by=request.user,
                )
            po.status = "received"
            po.save(update_fields=["status"])

        return Response({"status": "received"})


class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderItemSerializer
    filterset_fields = ["purchase_order"]

    def get_queryset(self):
        queryset = PurchaseOrderItem.objects.for_user(self.request.user).order_by(
            "-created_at"
        )
        purchase_order_id = self.request.query_params.get("purchase_order")
        if purchase_order_id:
            queryset = queryset.filter(purchase_order_id=purchase_order_id)
        return queryset

    def perform_create(self, serializer):
        po_id = self.request.data.get("purchase_order")
        po = PurchaseOrder.objects.for_user(self.request.user).get(id=po_id)
        if po.status != "draft":
            raise serializers.ValidationError(
                "Cannot add items to a non-draft purchase order."
            )
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        poi = self.get_object()
        if poi.purchase_order.status != "draft":
            raise serializers.ValidationError(
                "Cannot update items of a non-draft purchase order."
            )
        serializer.save(
            total_cost=serializer.validated_data["quantity"]
            * serializer.validated_data["unit_cost"]
        )

    def destroy(self, request, *args, **kwargs):
        poi = self.get_object()
        if poi.purchase_order.status != "draft":
            return Response(
                {"error": "Cannot delete items from a non-draft purchase order."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)
