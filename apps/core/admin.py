from django.contrib import admin
from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Brand', {'fields': ('site_name', 'tagline', 'logo', 'favicon')}),
        ('Contact', {'fields': ('contact_email', 'contact_phone', 'address', 'whatsapp_number')}),
        ('Social Media', {'fields': ('facebook_url', 'instagram_url', 'twitter_url', 'pinterest_url', 'youtube_url')}),
        ('Commerce', {'fields': ('currency', 'currency_symbol', 'free_shipping_threshold', 'flat_shipping_rate')}),
        ('Payment Methods', {'fields': ('razorpay_enabled', 'cod_enabled')}),
        ('Tax Settings', {'fields': ('tax_enabled', 'tax_label', 'tax_percentage', 'prices_include_tax')}),
        ('Analytics', {'fields': ('google_analytics_id',)}),
        ('Maintenance', {'fields': ('maintenance_mode', 'maintenance_message')}),
        ('SEO', {'fields': ('meta_title', 'meta_description', 'meta_keywords')}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()
