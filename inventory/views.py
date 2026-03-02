# inventory/views.py
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Product, Stock
from .serializers import ProductSerializer, StockSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "sku", "base_unit"]

    def get_queryset(self):
        # Use the custom manager to filter by current user
        return Product.objects.for_user(self.request.user).order_by("name")

    def perform_create(self, serializer):
        # Automatically set created_by to current user
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


class StockViewSet(viewsets.ModelViewSet):
    serializer_class = StockSerializer

    def get_queryset(self):
        # Use the custom manager to filter by current user
        return Stock.objects.for_user(self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        stock = self.get_object()
        if stock.remaining_quantity > 0:
            return Response(
                {"error": "Cannot delete stock with remaining quantity."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)
