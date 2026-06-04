from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Coupon, CouponUsage


class CouponUsageInline(admin.TabularInline):
    model = CouponUsage
    extra = 0
    readonly_fields = ["user", "order", "discount_amount", "created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "discount_display", "min_order_amount", "usage_display", "validity_badge", "is_active"]
    list_editable = ["is_active"]
    list_filter = ["is_active", "discount_type"]
    search_fields = ["code", "description"]
    readonly_fields = ["times_used", "created_at", "updated_at"]
    filter_horizontal = ["applicable_categories", "applicable_products"]
    inlines = [CouponUsageInline]
    actions = ["activate", "deactivate"]
    fieldsets = (
        ("Coupon", {
            "fields": ("code", "description", "is_active"),
            "description": "Give customers this <b>code</b> to enter at the cart or checkout. Keep it short and memorable (e.g. WELCOME10).",
        }),
        ("Discount", {
            "fields": ("discount_type", "discount_value", "max_discount"),
            "description": "Percentage: discount_value is the % (use max_discount to cap it). Fixed: discount_value is the ₹ amount off.",
        }),
        ("Conditions", {"fields": ("min_order_amount", "usage_limit", "usage_limit_per_user", "valid_from", "valid_until")}),
        ("Restrict to (optional)", {"fields": ("applicable_categories", "applicable_products"), "classes": ("collapse",)}),
        ("Stats", {"fields": ("times_used", "created_at", "updated_at")}),
    )

    def discount_display(self, obj):
        if obj.discount_type == "percentage":
            return f"{obj.discount_value:g}% off"
        if obj.discount_type == "fixed":
            return f"₹{obj.discount_value:g} off"
        return "Free shipping"
    discount_display.short_description = "Discount"

    def usage_display(self, obj):
        if obj.usage_limit:
            return f"{obj.times_used} / {obj.usage_limit}"
        return f"{obj.times_used} used"
    usage_display.short_description = "Usage"

    def validity_badge(self, obj):
        valid, msg = obj.is_valid()
        color = "#16a34a" if valid else "#dc2626"
        label = "Active" if valid else msg
        return format_html("<span style='color:{};font-weight:600'>●</span> {}", color, label)
    validity_badge.short_description = "Status"

    @admin.action(description="Activate selected coupons")
    def activate(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} coupon(s) activated.")

    @admin.action(description="Deactivate selected coupons")
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} coupon(s) deactivated.")
