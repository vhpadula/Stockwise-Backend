from django.urls import path
from .views import (
    FinancialSummaryView,
    ProductFinancialView,
    TimelineView,
    TopProductsView,
)

urlpatterns = [
    path("summary/", FinancialSummaryView.as_view(), name="financial-summary"),
    path("products/", ProductFinancialView.as_view(), name="financial-products"),
    path("timeline/", TimelineView.as_view(), name="financial-timeline"),
    path("top-products/", TopProductsView.as_view(), name="financial-top-products"),
]
