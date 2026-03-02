# inventory/views.py
from rest_framework import viewsets, filters, status
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Stock
from .serializers import (
    ProductSerializer,
    StockMetadataUpdateSerializer,
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
