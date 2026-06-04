from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    class Meta:
        abstract = True


class SiteSettings(TimeStampedModel):
    site_name = models.CharField(max_length=100, default='Aura Archives')
    tagline = models.CharField(max_length=200, default='Light That Preserves Moments')
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    pinterest_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    google_analytics_id = models.CharField(max_length=50, blank=True)
    razorpay_enabled = models.BooleanField(default=True)
    cod_enabled = models.BooleanField(default=True, help_text='Allow Cash on Delivery at checkout')
    currency = models.CharField(max_length=10, default='INR')
    currency_symbol = models.CharField(max_length=5, default='₹')
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    flat_shipping_rate = models.DecimalField(max_digits=8, decimal_places=2, default=49, help_text='Shipping charge below the free-shipping threshold')
    # Tax
    tax_enabled = models.BooleanField(default=False)
    tax_label = models.CharField(max_length=30, default='GST')
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='e.g. 18 for 18%')
    prices_include_tax = models.BooleanField(default=True, help_text='If on, displayed prices already include tax (a note is shown). If off, tax is added at checkout.')
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    @classmethod
    def get_settings(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings
