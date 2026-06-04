from django.contrib import admin
from .models import SEOSettings


@admin.register(SEOSettings)
class SEOSettingsAdmin(admin.ModelAdmin):
    list_display = ["page_path", "meta_title", "no_index"]
    search_fields = ["page_path"]
