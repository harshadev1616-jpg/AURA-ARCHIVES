from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel
from apps.products.models import Product


class Wishlist(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, blank=True, related_name='wishlisted_by')

    def __str__(self):
        return f"{self.user.email}'s Wishlist"

    def get_or_create_for_user(user):
        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        return wishlist
