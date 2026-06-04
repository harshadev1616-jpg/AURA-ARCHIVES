from django.contrib import admin
from .models import BlogPost, BlogCategory


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "category", "status", "is_featured", "view_count", "published_at"]
    list_filter = ["status", "is_featured", "category"]
    list_editable = ["status", "is_featured"]
    prepopulated_fields = {"slug": ["title"]}
    search_fields = ["title", "content"]
    readonly_fields = ["view_count"]
