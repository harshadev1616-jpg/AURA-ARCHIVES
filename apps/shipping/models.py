from django.db import models
from apps.core.models import TimeStampedModel


class ShippingZone(TimeStampedModel):
    name = models.CharField(max_length=100)
    states = models.TextField(help_text='Comma-separated state names')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ShippingMethod(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE, related_name='methods', null=True, blank=True)
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    min_order_for_free = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_days_min = models.PositiveIntegerField(default=3)
    estimated_days_max = models.PositiveIntegerField(default=7)
    is_active = models.BooleanField(default=True)
    is_cod_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['base_price']

    def __str__(self):
        return self.name

    def calculate_price(self, order_total):
        if self.min_order_for_free and order_total >= self.min_order_for_free:
            return 0
        return self.base_price
