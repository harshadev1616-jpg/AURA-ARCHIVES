from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel
from apps.products.models import Product, ProductVariant


class Order(TimeStampedModel):
    STATUS_CHOICES = (
        ('pending', 'Pending'), ('confirmed', 'Confirmed'), ('processing', 'Processing'),
        ('shipped', 'Shipped'), ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'), ('cancelled', 'Cancelled'),
        ('refund_requested', 'Refund Requested'), ('refunded', 'Refunded'), ('returned', 'Returned'),
    )
    PAYMENT_STATUS = (
        ('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed'),
        ('refunded', 'Refunded'), ('partially_refunded', 'Partially Refunded'),
    )
    PAYMENT_METHODS = (('razorpay', 'Razorpay'), ('cod', 'Cash on Delivery'), ('upi', 'UPI'))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='razorpay')
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=200, blank=True)
    shipping_full_name = models.CharField(max_length=200)
    shipping_phone = models.CharField(max_length=20)
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_pincode = models.CharField(max_length=10)
    shipping_country = models.CharField(max_length=100, default='India')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_charge = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    gift_message = models.TextField(blank=True)
    is_gift = models.BooleanField(default=False)
    tracking_number = models.CharField(max_length=100, blank=True)
    courier_name = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    stock_deducted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import random, string
            self.order_number = 'AA' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)

    def can_cancel(self):
        return self.status in ('pending', 'confirmed')

    def can_return(self):
        return self.status == 'delivered'


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    variant_info = models.CharField(max_length=200, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    product_image = models.URLField(blank=True)

    @property
    def line_total(self):
        return (self.price or 0) * (self.quantity or 0)


class OrderStatusHistory(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['created_at']


class CartItem(TimeStampedModel):
    session_key = models.CharField(max_length=40, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    reminder_sent = models.BooleanField(default=False)

    @property
    def price(self):
        if self.variant:
            return self.variant.final_price
        return self.product.price

    @property
    def total(self):
        return self.price * self.quantity


class ReturnRequest(TimeStampedModel):
    STATUS_CHOICES = (('pending','Pending'),('approved','Approved'),('rejected','Rejected'),('completed','Completed'))
    REASON_CHOICES = (
        ('defective','Defective/Damaged'),('wrong_item','Wrong Item'),
        ('not_as_described','Not as Described'),('changed_mind','Changed Mind'),('other','Other'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
