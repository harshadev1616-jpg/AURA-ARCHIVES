import os
import uuid
from django.utils.text import slugify


def unique_slug(instance, value, slug_field='slug'):
    slug = slugify(value)
    model = instance.__class__
    unique = slug
    counter = 1
    while model.objects.filter(**{slug_field: unique}).exclude(pk=instance.pk).exists():
        unique = f"{slug}-{counter}"
        counter += 1
    return unique


def upload_to(folder):
    def _upload_to(instance, filename):
        ext = filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        return os.path.join(folder, filename)
    return _upload_to
