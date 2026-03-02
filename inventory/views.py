# inventory/views.py
from rest_framework import viewsets, filters, status
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Stock, StockMovement
from .serializers import (
    ProductSerializer,
    StockMetadataUpdateSerializer,
    StockMovementSerializer,
    StockSerializer,
)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "sku", "base_unit"]

    def get_queryset(self):
        return Product.objects.for_user(self.request.user).order_by("name")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        if product.stocks.exists():
            return Response(
                {"error": "Cannot delete product with existing stocks."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class StockViewSet(UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["lot_number", "product__name"]
    filterset_fields = ["expiration_date", "product"]
    ordering_fields = ["created_at", "expiration_date"]

    def get_queryset(self):
        return (
            Stock.objects.for_user(self.request.user)
            .select_related("product")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "partial_update":
            return StockMetadataUpdateSerializer
        return StockSerializer

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for Stock Movements.
    """

    serializer_class = StockMovementSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["stock", "sales_order_item", "stock__product"]
    ordering_fields = ["created_at", "quantity", "cost_per_unit"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = StockMovement.objects.for_user(self.request.user)

        # Optional date range filtering
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset
