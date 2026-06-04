from django.contrib import admin
from .models import PageView, ProductView


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ["path", "user", "ip_address", "created_at"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at"]
