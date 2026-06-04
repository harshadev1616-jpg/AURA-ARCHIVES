from django.core.management.base import BaseCommand


REVIEWS = [
    ("Priya", "S", 5, "Absolutely divine", "The throw is incredible — one candle scents my whole living room. It genuinely feels like a little ritual every evening."),
    ("Ananya", "M", 5, "My new signature scent", "I've repurchased three times now. Burns clean, lasts forever, and the packaging is so beautiful I kept the box."),
    ("Rhea", "K", 5, "Gifted and loved", "Bought the gift set for my sister and she was obsessed. The little note inside was such a thoughtful touch."),
    ("Devika", "N", 4, "Calm in a jar", "Lavender Dreams is exactly what I needed for winding down. Subtle but lingers beautifully."),
    ("Sara", "P", 5, "Worth every rupee", "You can tell these are hand-poured. The finish is flawless and the scent is layered, not cheap or synthetic."),
    ("Meera", "J", 5, "The moment it preserves", "Sunlit Bloom takes me straight to a summer afternoon. Aura Archives really gets the storytelling right."),
]


class Command(BaseCommand):
    help = "Seed approved customer reviews across demo products for the testimonials section."

    def handle(self, *args, **options):
        from apps.accounts.models import User
        from apps.products.models import Product
        from apps.reviews.models import Review

        products = list(Product.objects.filter(is_active=True))
        if not products:
            self.stdout.write("No products — run import_aura_images first.")
            return
        created = 0
        for i, (first, last, rating, title, body) in enumerate(REVIEWS):
            email = f"{first.lower()}.{last.lower()}@reviewers.aura"
            user, _ = User.objects.get_or_create(email=email, defaults={"first_name": first, "last_name": last})
            product = products[i % len(products)]
            _, made = Review.objects.get_or_create(
                product=product, user=user,
                defaults={"rating": rating, "title": title, "body": body,
                          "is_approved": True, "is_verified_purchase": True, "helpful_count": (i * 3) % 11},
            )
            if made:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} approved reviews (testimonials will now show)."))
