import csv
from django.contrib import admin
from django.http import HttpResponse
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, LoyaltyTransaction


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "first_name", "last_name", "loyalty_points", "referral_code", "is_active", "is_staff", "date_joined"]
    list_filter = ["is_active", "is_staff", "newsletter_subscribed"]
    actions = ["export_customers_csv"]

    @admin.action(description="⬇ Export selected customers to CSV")
    def export_customers_csv(self, request, queryset):
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="aura-customers.csv"'
        w = csv.writer(resp)
        w.writerow(["Email", "First name", "Last name", "Phone", "Loyalty points",
                    "Referral code", "Newsletter", "Joined", "Orders"])
        for u in queryset:
            w.writerow([u.email, u.first_name, u.last_name, u.phone, u.loyalty_points,
                        u.referral_code, "Yes" if u.newsletter_subscribed else "No",
                        u.date_joined.strftime("%Y-%m-%d"), u.orders.count()])
        self.message_user(request, f"Exported {queryset.count()} customer(s).")
        return resp
    search_fields = ["email", "first_name", "last_name", "referral_code"]
    ordering = ["-date_joined"]
    readonly_fields = ["loyalty_points", "referral_code"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone", "avatar", "date_of_birth")}),
        ("Loyalty & Referrals", {"fields": ("loyalty_points", "referral_code", "referred_by", "referral_rewarded")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Preferences", {"fields": ("newsletter_subscribed",)}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "password1", "password2")}),)


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ["user", "points", "reason", "order", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__email", "reason"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["user", "full_name", "city", "state", "is_default"]
