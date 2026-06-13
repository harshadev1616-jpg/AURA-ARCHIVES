from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class EmailLog(TimeStampedModel):
    STATUS_CHOICES = (('pending','Pending'),('sent','Sent'),('failed','Failed'))
    to_email = models.EmailField()
    subject = models.CharField(max_length=200)
    template = models.CharField(max_length=100)
    context_data = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} -> {self.to_email}"


class Notification(TimeStampedModel):
    TYPES = (
        ('order_placed','Order Placed'),('order_shipped','Order Shipped'),
        ('order_delivered','Order Delivered'),('order_cancelled','Order Cancelled'),
        ('review_approved','Review Approved'),('wishlist_back_in_stock','Back in Stock'),
        ('admin_new_order', 'Admin New Order'), ('system','System'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.URLField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.title}"
