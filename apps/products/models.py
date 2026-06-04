from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.core.utils import upload_to, unique_slug


class Category(TimeStampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    tagline = models.CharField(max_length=200, blank=True, help_text='A short, evocative line for the collection')
    description = models.TextField(blank=True)
    story = models.TextField(blank=True, help_text='The narrative behind this collection')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, help_text='Tailwind/Heroicon class')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category', kwargs={'slug': self.slug})

    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()


class Tag(TimeStampedModel):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(TimeStampedModel, SoftDeleteModel):
    FRAGRANCE_STRENGTH = (
        ('light', 'Light'),
        ('medium', 'Medium'),
        ('strong', 'Strong'),
        ('intense', 'Intense'),
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    tags = models.ManyToManyField(Tag, blank=True)
    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    ingredients = models.TextField(blank=True)
    fragrance_notes = models.CharField(max_length=300, blank=True)
    fragrance_strength = models.CharField(max_length=10, choices=FRAGRANCE_STRENGTH, blank=True)
    # ----- Storytelling -----
    moment = models.CharField(max_length=200, blank=True, help_text='The moment this candle preserves, e.g. "Sunday mornings with nowhere to be"')
    story = models.TextField(blank=True, help_text='The narrative / inspiration behind this candle')
    ritual = models.TextField(blank=True, help_text='How to enjoy it — the lighting ritual')
    notes_top = models.CharField(max_length=200, blank=True, help_text='Top / opening notes')
    notes_heart = models.CharField(max_length=200, blank=True, help_text='Heart / middle notes')
    notes_base = models.CharField(max_length=200, blank=True, help_text='Base / dry-down notes')
    burn_time_min = models.PositiveIntegerField(null=True, blank=True, help_text='Minimum burn time in hours')
    burn_time_max = models.PositiveIntegerField(null=True, blank=True, help_text='Maximum burn time in hours')
    wax_type = models.CharField(max_length=100, default='100% Natural Soy Wax', blank=True)
    wick_type = models.CharField(max_length=100, default='Cotton Wick', blank=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text='Weight in grams')
    dimensions = models.CharField(max_length=100, blank=True, help_text='e.g. 8cm x 8cm x 10cm')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    track_inventory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=True)
    is_gift_ready = models.BooleanField(default=True)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    care_instructions = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        if not self.sku:
            import uuid
            self.sku = f"AA-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def discount_percentage(self):
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0

    @property
    def is_in_stock(self):
        if not self.track_inventory:
            return True
        return self.stock > 0

    @property
    def is_low_stock(self):
        return self.track_inventory and 0 < self.stock <= self.low_stock_threshold

    @property
    def burn_time_display(self):
        if self.burn_time_min and self.burn_time_max:
            return f"{self.burn_time_min}-{self.burn_time_max} hours"
        if self.burn_time_min:
            return f"{self.burn_time_min}+ hours"
        return ''

    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_primary', 'sort_order']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVariant(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, help_text='e.g. Size, Scent')
    value = models.CharField(max_length=100, help_text='e.g. Small, Lavender')
    price_adjustment = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True)
    image = models.ForeignKey(ProductImage, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['product', 'name', 'value']

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"

    @property
    def final_price(self):
        return self.product.price + self.price_adjustment


class StockNotification(TimeStampedModel):
    """A 'notify me when back in stock' request."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_notifications')
    email = models.EmailField()
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    is_notified = models.BooleanField(default=False)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'email']

    def __str__(self):
        return f"{self.email} → {self.product.name}"
