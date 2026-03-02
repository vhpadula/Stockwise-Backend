from .models import Stock, StockMovement


def add_stock(stock: Stock, quantity: float, unit_cost: float, sales_order_item=None):
    """
    Add stock and create a corresponding StockMovement.
    sales_order_item is optional and only set when stock is consumed in a sale.
    """
    # Update remaining_quantity
    stock.remaining_quantity += quantity
    stock.save()

    # Log the movement
    StockMovement.objects.create(
        stock=stock,
        sales_order_item=sales_order_item,
        quantity=quantity,
        cost_per_unit=unit_cost,
    )
