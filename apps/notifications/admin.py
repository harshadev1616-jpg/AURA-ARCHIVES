from django.contrib import admin
from .models import EmailLog, Notification


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ["subject", "to_email", "status", "created_at"]
    list_filter = ["status"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "notification_type", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read"]
