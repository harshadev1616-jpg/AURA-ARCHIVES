from django.db.models import Q, Avg
from .models import Product


def search_products(query):
    if not query:
        return Product.objects.filter(is_active=True)
    return Product.objects.filter(is_active=True).filter(
        Q(name__icontains=query) | Q(description__icontains=query) | Q(fragrance_notes__icontains=query)
    )


def get_recently_viewed(request, limit=4):
    viewed_ids = request.session.get("recently_viewed", [])
    return Product.objects.filter(pk__in=viewed_ids, is_active=True)[:limit]


def get_related_products(product, limit=4):
    return Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:limit]
