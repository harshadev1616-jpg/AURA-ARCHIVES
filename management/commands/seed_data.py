from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed the database with initial site settings, pages, coupons, shipping methods, and content."

    def handle(self, *args, **options):
        from apps.core.models import SiteSettings
        from apps.cms.models import Page, Announcement, Banner
        from apps.coupons.models import Coupon
        from apps.shipping.models import ShippingMethod
        from apps.blog.models import BlogCategory, BlogPost
        from apps.accounts.models import User

        # Site Settings
        settings_obj = SiteSettings.get_settings()
        settings_obj.site_name = "Aura Archives"
        settings_obj.tagline = "Light That Preserves Moments"
        settings_obj.contact_email = "hello@aura-archives.com"
        settings_obj.contact_phone = "+91 98765 43210"
        settings_obj.whatsapp_number = "919876543210"
        settings_obj.instagram_url = "https://instagram.com/auraarchives"
        settings_obj.facebook_url = "https://facebook.com/auraarchives"
        settings_obj.free_shipping_threshold = 500
        settings_obj.meta_title = "Aura Archives - Handmade Luxury Soy Candles"
        settings_obj.meta_description = "Handcrafted luxury soy candles. Light That Preserves Moments. Floral, gift & home decor candles made in small batches."
        settings_obj.save()
        self.stdout.write("  + Site settings configured")

        # CMS Pages
        pages = [
            {"title": "About Us", "page_type": "about", "content": "Aura Archives crafts handmade luxury soy candles..."},
            {"title": "Shipping Policy", "page_type": "shipping", "content": "We ship across India. Free shipping on orders above Rs.500. Delivery in 3-7 business days."},
            {"title": "Return Policy", "page_type": "refund", "content": "Returns accepted within 7 days of delivery for defective products. Contact us to initiate a return."},
            {"title": "Privacy Policy", "page_type": "privacy", "content": "Your privacy matters. We never share your personal data with third parties."},
            {"title": "Terms of Service", "page_type": "terms", "content": "By using Aura Archives you agree to our terms and conditions."},
            {"title": "FAQ", "page_type": "faq", "content": "Q: How long do candles burn?\nA: Our candles burn for 25-60 hours depending on size.\n\nQ: Are they natural?\nA: Yes, 100% natural soy wax with cotton wicks."},
        ]
        for p in pages:
            Page.objects.get_or_create(title=p["title"], defaults={
                "page_type": p["page_type"], "content": p["content"],
                "is_active": True, "show_in_footer": True,
            })
        self.stdout.write(f"  + {len(pages)} CMS pages created")

        # Announcement
        Announcement.objects.get_or_create(
            message="Free shipping on all orders above Rs.500",
            defaults={"is_active": True, "link_text": "Shop Now", "link_url": "/shop/"}
        )

        # Coupons
        Coupon.objects.get_or_create(code="WELCOME10", defaults={
            "description": "10% off for new customers", "discount_type": "percentage",
            "discount_value": 10, "min_order_amount": 500, "max_discount": 200,
            "is_active": True, "valid_until": timezone.now() + timezone.timedelta(days=365),
        })
        Coupon.objects.get_or_create(code="AURA100", defaults={
            "description": "Flat Rs.100 off", "discount_type": "fixed",
            "discount_value": 100, "min_order_amount": 1000,
            "is_active": True, "valid_until": timezone.now() + timezone.timedelta(days=365),
        })
        self.stdout.write("  + 2 coupons created (WELCOME10, AURA100)")

        # Shipping Methods
        ShippingMethod.objects.get_or_create(name="Standard Delivery", defaults={
            "base_price": 49, "min_order_for_free": 500,
            "estimated_days_min": 3, "estimated_days_max": 7, "is_active": True,
        })
        ShippingMethod.objects.get_or_create(name="Express Delivery", defaults={
            "base_price": 99, "min_order_for_free": 2000,
            "estimated_days_min": 1, "estimated_days_max": 3, "is_active": True,
        })
        self.stdout.write("  + 2 shipping methods created")

        # Blog
        blog_cat, _ = BlogCategory.objects.get_or_create(name="Candle Care")
        BlogPost.objects.get_or_create(title="How to Make Your Candle Last Longer", defaults={
            "category": blog_cat,
            "excerpt": "Simple tips to maximize the burn time and fragrance of your soy candles.",
            "content": "Always trim your wick to 1/4 inch before lighting. Let the wax pool reach the edges on the first burn to prevent tunneling. Keep away from drafts and never burn for more than 4 hours at a time.",
            "status": "published", "is_featured": True, "published_at": timezone.now(),
        })
        self.stdout.write("  + Sample blog post created")

        self.stdout.write(self.style.SUCCESS("Seed data complete! Now run: python manage.py import_aura_images"))
