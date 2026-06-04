from decimal import Decimal
from apps.products.models import Product, ProductVariant


class Cart:
    # Bundle & save: buy this many candles (any mix) and save this rate
    BUNDLE_THRESHOLD = 3
    BUNDLE_RATE = Decimal('0.10')

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, variant=None, quantity=1, override_quantity=False):
        product_id = str(product.id)
        variant_id = str(variant.id) if variant else 'none'
        key = f"{product_id}_{variant_id}"

        if key not in self.cart:
            self.cart[key] = {
                'product_id': product_id,
                'variant_id': variant_id,
                'quantity': 0,
                'price': str(variant.final_price if variant else product.price),
            }

        if override_quantity:
            self.cart[key]['quantity'] = quantity
        else:
            self.cart[key]['quantity'] += quantity

        self.save()

    def remove(self, product_id, variant_id='none'):
        key = f"{product_id}_{variant_id}"
        if key in self.cart:
            del self.cart[key]
            self.save()

    def update(self, product_id, variant_id, quantity):
        key = f"{product_id}_{variant_id}"
        if key in self.cart:
            self.cart[key]['quantity'] = quantity
            if quantity <= 0:
                del self.cart[key]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        del self.session['cart']
        self.save()

    def __iter__(self):
        product_ids = [v['product_id'] for v in self.cart.values()]
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for item in cart.values():
            try:
                item['product'] = products.get(id=item['product_id'])
                if item['variant_id'] != 'none':
                    item['variant'] = ProductVariant.objects.get(id=item['variant_id'])
                else:
                    item['variant'] = None
                item['price'] = Decimal(item['price'])
                item['total_price'] = item['price'] * item['quantity']
                yield item
            except (Product.DoesNotExist, ProductVariant.DoesNotExist):
                pass

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    @property
    def total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    @property
    def subtotal(self):
        return self.total_price

    @property
    def qualifies_for_bundle(self):
        return len(self) >= self.BUNDLE_THRESHOLD

    @property
    def items_to_next_bundle(self):
        """How many more candles needed to unlock the bundle saving (0 if already qualified)."""
        remaining = self.BUNDLE_THRESHOLD - len(self)
        return remaining if remaining > 0 else 0

    @property
    def bundle_discount(self):
        if self.qualifies_for_bundle:
            return (self.total_price * self.BUNDLE_RATE).quantize(Decimal('0.01'))
        return Decimal('0.00')

    @property
    def bundle_rate_percent(self):
        return int(self.BUNDLE_RATE * 100)

    @property
    def total_after_bundle(self):
        return self.total_price - self.bundle_discount

    def is_empty(self):
        return len(self.cart) == 0
