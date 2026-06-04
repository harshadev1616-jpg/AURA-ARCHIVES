from django.db import models
from apps.core.models import TimeStampedModel


class SEOSettings(TimeStampedModel):
    page_path = models.CharField(max_length=200, unique=True)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    og_title = models.CharField(max_length=200, blank=True)
    og_description = models.TextField(blank=True)
    og_image = models.ImageField(upload_to='seo/', blank=True, null=True)
    canonical_url = models.URLField(blank=True)
    no_index = models.BooleanField(default=False)
    no_follow = models.BooleanField(default=False)
    schema_markup = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'SEO Settings'
        verbose_name_plural = 'SEO Settings'

    def __str__(self):
        return self.page_path
