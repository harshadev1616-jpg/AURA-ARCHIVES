from django.contrib import admin
from .models import Page, Banner, Announcement, Popup


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "page_type", "is_active", "show_in_footer", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    prepopulated_fields = {"slug": ["title"]}


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["title", "position", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    list_filter = ["position", "is_active"]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["message", "is_active", "sort_order", "valid_until"]
    list_editable = ["is_active", "sort_order"]


@admin.register(Popup)
class PopupAdmin(admin.ModelAdmin):
    list_display = ["title", "trigger", "is_active"]
    list_editable = ["is_active"]
