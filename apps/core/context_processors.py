from .models import SiteSettings
from apps.orders.cart import Cart


def site_settings(request):
    try:
        return {'site_settings': SiteSettings.get_settings()}
    except Exception:
        return {'site_settings': None}


def cart_info(request):
    cart = Cart(request)
    return {
        'cart': cart,
        'cart_count': len(cart),
    }


def recently_viewed(request):
    try:
        ids = request.session.get('recently_viewed', [])
        if not ids:
            return {'recently_viewed_products': []}
        from apps.products.models import Product
        products = Product.objects.filter(pk__in=ids, is_active=True).prefetch_related('images')
        by_id = {p.pk: p for p in products}
        ordered = [by_id[pid] for pid in ids if pid in by_id]
        return {'recently_viewed_products': ordered[:8]}
    except Exception:
        return {'recently_viewed_products': []}
