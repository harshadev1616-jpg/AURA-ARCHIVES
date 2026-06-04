from django.db import models
from apps.core.models import TimeStampedModel
from django.utils.text import slugify


class Page(TimeStampedModel):
    PAGE_TYPES = (
        ('about', 'About'), ('contact', 'Contact'), ('faq', 'FAQ'),
        ('privacy', 'Privacy Policy'), ('terms', 'Terms of Service'),
        ('refund', 'Refund Policy'), ('shipping', 'Shipping Policy'), ('custom', 'Custom'),
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, default='custom')
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    show_in_footer = models.BooleanField(default=True)
    show_in_header = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('cms:page', kwargs={'slug': self.slug})


class Banner(TimeStampedModel):
    BANNER_POSITIONS = (
        ('hero', 'Hero Banner'), ('home_featured', 'Home Featured'),
        ('sidebar', 'Sidebar'), ('popup', 'Popup'), ('announcement', 'Announcement Bar'),
    )
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='banners/', blank=True, null=True)
    image_mobile = models.ImageField(upload_to='banners/', blank=True, null=True)
    link_url = models.URLField(blank=True)
    link_text = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=20, choices=BANNER_POSITIONS, default='hero')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    background_color = models.CharField(max_length=20, blank=True)
    text_color = models.CharField(max_length=20, blank=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['position', 'sort_order']

    def __str__(self):
        return f"{self.title} ({self.position})"


class Announcement(TimeStampedModel):
    message = models.CharField(max_length=300)
    link_url = models.URLField(blank=True)
    link_text = models.CharField(max_length=50, blank=True)
    background_color = models.CharField(max_length=20, default='#C9A86A')
    text_color = models.CharField(max_length=20, default='#FFFFFF')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.message


class Popup(TimeStampedModel):
    TRIGGER_CHOICES = (
        ('on_load', 'On Page Load'), ('exit_intent', 'Exit Intent'), ('time_delay', 'Time Delay'),
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='popups/', blank=True, null=True)
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES, default='time_delay')
    delay_seconds = models.PositiveIntegerField(default=5)
    show_once = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    show_on_pages = models.CharField(max_length=500, blank=True, help_text='Comma-separated page slugs, leave blank for all pages')

    def __str__(self):
        return self.title
