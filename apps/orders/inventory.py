"""Centralised stock validation + commit/release for orders."""
from django.db import transaction
from django.db.models import F
from apps.products.models import Product, ProductVariant

# Statuses where stock is considered "taken" (a real/pending sale)
COMMITTED_STATUSES = {"confirmed", "processing", "shipped", "out_for_delivery", "delivered"}
# Statuses where stock should be returned to inventory
RELEASED_STATUSES = {"cancelled", "refunded", "returned"}


def available_stock(product, variant=None):
    """How many units can still be sold. None == unlimited (inventory not tracked)."""
    if variant is not None:
        return variant.stock
    if not product.track_inventory:
        return None
    return product.stock


def check_availability(product, variant, requested_qty):
    """Return (ok, available, message)."""
    avail = available_stock(product, variant)
    if avail is None:
        return True, None, ""
    if avail <= 0:
        return False, 0, "Out of stock"
    if requested_qty > avail:
        return False, avail, f"Only {avail} left in stock"
    return True, avail, ""


def deduct_for_order(order):
    """Reduce stock for each line. Idempotent via order.stock_deducted."""
    from .models import Order
    if order.stock_deducted:
        return
    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        if locked.stock_deducted:
            return
        items = list(order.items.select_related("product", "variant"))
        if not items:
            return  # no lines yet (e.g. inline items not saved) — don't flag; deduct on a later transition
        for item in items:
            if item.variant_id:
                ProductVariant.objects.filter(pk=item.variant_id).update(
                    stock=Greatest0(F("stock") - item.quantity))
            if item.product_id:
                Product.objects.filter(pk=item.product_id, track_inventory=True).update(
                    stock=Greatest0(F("stock") - item.quantity))
        Order.objects.filter(pk=order.pk).update(stock_deducted=True)


def restore_for_order(order):
    """Return stock to inventory (e.g. on cancellation). Idempotent."""
    from .models import Order
    if not order.stock_deducted:
        return
    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        if not locked.stock_deducted:
            return
        for item in order.items.select_related("product", "variant"):
            if item.variant_id:
                ProductVariant.objects.filter(pk=item.variant_id).update(stock=F("stock") + item.quantity)
            if item.product_id:
                Product.objects.filter(pk=item.product_id, track_inventory=True).update(stock=F("stock") + item.quantity)
        Order.objects.filter(pk=order.pk).update(stock_deducted=False)


def Greatest0(expr):
    """Clamp an F expression at 0 so stock never goes negative."""
    from django.db.models.functions import Greatest
    from django.db.models import Value
    return Greatest(expr, Value(0))
