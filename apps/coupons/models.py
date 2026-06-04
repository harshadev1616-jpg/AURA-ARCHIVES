from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class Coupon(TimeStampedModel):
    DISCOUNT_TYPES = (('percentage', 'Percentage'), ('fixed', 'Fixed Amount'), ('free_shipping', 'Free Shipping'))

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(max_length=15, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text='Max discount for percentage type')
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text='Total usage limit')
    usage_limit_per_user = models.PositiveIntegerField(default=1)
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    applicable_categories = models.ManyToManyField('products.Category', blank=True)
    applicable_products = models.ManyToManyField('products.Product', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False, "Coupon is not active"
        if now < self.valid_from:
            return False, "Coupon is not yet valid"
        if self.valid_until and now > self.valid_until:
            return False, "Coupon has expired"
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, "Coupon usage limit reached"
        return True, "Valid"

    def calculate_discount(self, subtotal):
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / 100
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return discount
        elif self.discount_type == 'fixed':
            return min(self.discount_value, subtotal)
        return 0


class CouponUsage(TimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2)
