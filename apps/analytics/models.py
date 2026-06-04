from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class PageView(TimeStampedModel):
    path = models.CharField(max_length=500)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.path} - {self.created_at}"


class ProductView(TimeStampedModel):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ['-created_at']
