from django.contrib import admin
from .models import ShippingZone, ShippingMethod


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ["name", "base_price", "min_order_for_free", "is_active"]
    list_editable = ["base_price", "is_active"]
