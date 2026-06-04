import requests
import uuid
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings

PRODUCT_DATA = [
    {"name": "Daisy Glow Set", "category": "Gift Sets", "description": "Hand-poured daisy soy candle collection. Three luxury soy candles infused with fresh daisy fragrance.", "short_description": "Hand-poured daisy soy candle set - 3 pieces", "fragrance_notes": "Fresh Daisy, White Musk, Light Citrus", "price": "1299.00", "compare_price": "1599.00", "stock": 25, "burn_time_min": 35, "burn_time_max": 45, "is_featured": True, "is_bestseller": True, "search_query": "candle gift set luxury"},
    {"name": "Sunlit Bloom", "category": "Floral", "description": "Sun-drenched summer garden fragrance. A luxury soy candle with 50-hour burn time.", "short_description": "Warm floral soy candle with 50-hour burn time", "fragrance_notes": "Sunflower, Jasmine, Warm Amber, Vanilla", "price": "799.00", "compare_price": "999.00", "stock": 40, "burn_time_min": 45, "burn_time_max": 55, "is_featured": True, "is_bestseller": True, "search_query": "floral candle luxury home"},
    {"name": "Blush Heart Candle", "category": "Gift Candles", "description": "Heart-shaped candle in blush pink with rose and peony fragrances.", "short_description": "Heart-shaped blush pink soy candle", "fragrance_notes": "Rose, Peony, Pink Sugar, Soft Musk", "price": "649.00", "compare_price": "849.00", "stock": 30, "burn_time_min": 25, "burn_time_max": 35, "is_featured": True, "is_new": True, "search_query": "pink candle romantic gift"},
    {"name": "Lavender Dreams", "category": "Wellness", "description": "Calming lavender soy candle for meditation, yoga and relaxation.", "short_description": "Calming lavender soy candle for relaxation", "fragrance_notes": "French Lavender, Chamomile, Eucalyptus, Clean Cotton", "price": "599.00", "compare_price": "749.00", "stock": 50, "burn_time_min": 40, "burn_time_max": 50, "is_bestseller": True, "search_query": "lavender candle spa wellness"},
    {"name": "Petal Crown Collection", "category": "Floral", "description": "Artisanal floral crown candle with hand-placed dried flowers and botanicals.", "short_description": "Artisanal candle with dried flower crown", "fragrance_notes": "Wildflower, Rose Hip, Bergamot, Green Tea", "price": "1099.00", "compare_price": "1299.00", "stock": 15, "burn_time_min": 30, "burn_time_max": 40, "is_featured": True, "is_new": True, "search_query": "dried flowers candle aesthetic"},
    {"name": "Vanilla Amber Luxe", "category": "Classic", "description": "Warm vanilla and rich amber soy candle. Our best-selling fragrance.", "short_description": "Warm vanilla and amber luxury soy candle", "fragrance_notes": "Madagascar Vanilla, Warm Amber, Sandalwood, Tonka Bean", "price": "899.00", "compare_price": "1099.00", "stock": 35, "burn_time_min": 50, "burn_time_max": 60, "is_bestseller": True, "search_query": "vanilla candle luxury warm"},
    {"name": "Rose Garden Gift Box", "category": "Gift Sets", "description": "Luxury 3-piece rose candle gift set in a beautiful keepsake box.", "short_description": "Premium 3-piece rose candle gift set", "fragrance_notes": "Turkish Rose, Bulgarian Rose, White Jasmine, Oud", "price": "2199.00", "compare_price": "2599.00", "stock": 20, "burn_time_min": 35, "burn_time_max": 45, "is_featured": True, "is_gift_ready": True, "search_query": "rose candle gift box premium"},
    {"name": "Midnight Bloom", "category": "Classic", "description": "Mysterious night-blooming florals with woody undertones.", "short_description": "Mysterious night-blooming floral soy candle", "fragrance_notes": "Night Jasmine, Black Rose, Dark Amber, Cedarwood", "price": "749.00", "compare_price": "949.00", "stock": 28, "burn_time_min": 40, "burn_time_max": 50, "is_new": True, "search_query": "dark floral candle elegant"},
]

CATEGORY_DATA = [
    {"name": "Gift Sets", "description": "Curated candle gift sets for every occasion", "sort_order": 1},
    {"name": "Floral", "description": "Beautiful floral-scented soy candles", "sort_order": 2},
    {"name": "Gift Candles", "description": "Perfect candles for gifting", "sort_order": 3},
    {"name": "Wellness", "description": "Calming candles for relaxation and meditation", "sort_order": 4},
    {"name": "Classic", "description": "Our signature classic fragrances", "sort_order": 5},
]


def fetch_image(query, unsplash_key=None, pexels_key=None):
    if unsplash_key:
        try:
            resp = requests.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 1, "orientation": "squarish"},
                headers={"Authorization": f"Client-ID {unsplash_key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    img_resp = requests.get(results[0]["urls"]["regular"], timeout=15)
                    if img_resp.status_code == 200:
                        return img_resp.content
        except Exception:
            pass
    if pexels_key:
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "per_page": 1},
                headers={"Authorization": pexels_key},
                timeout=10,
            )
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                if photos:
                    img_resp = requests.get(photos[0]["src"]["large"], timeout=15)
                    if img_resp.status_code == 200:
                        return img_resp.content
        except Exception:
            pass
    return None


class Command(BaseCommand):
    help = "Import demo products for Aura Archives with images from Unsplash/Pexels"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear existing products before importing")
        parser.add_argument("--no-images", action="store_true", help="Skip image downloading")

    def handle(self, *args, **options):
        from apps.products.models import Product, Category, ProductImage

        unsplash_key = getattr(settings, "UNSPLASH_ACCESS_KEY", "")
        pexels_key = getattr(settings, "PEXELS_API_KEY", "")

        if options["clear"]:
            self.stdout.write("Clearing existing products...")
            Product.all_objects.all().delete()
            Category.objects.all().delete()

        self.stdout.write("Creating categories...")
        categories = {}
        for cat_data in CATEGORY_DATA:
            cat, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={"description": cat_data["description"], "sort_order": cat_data["sort_order"]}
            )
            categories[cat_data["name"]] = cat
            if created:
                self.stdout.write(f"  + Category: {cat.name}")

        self.stdout.write(f"Creating {len(PRODUCT_DATA)} products...")
        for prod_data in PRODUCT_DATA:
            category = categories.get(prod_data["category"])
            product, created = Product.objects.get_or_create(
                name=prod_data["name"],
                defaults={
                    "category": category,
                    "description": prod_data["description"],
                    "short_description": prod_data["short_description"],
                    "fragrance_notes": prod_data["fragrance_notes"],
                    "price": prod_data["price"],
                    "compare_price": prod_data.get("compare_price"),
                    "stock": prod_data.get("stock", 20),
                    "burn_time_min": prod_data.get("burn_time_min", 30),
                    "burn_time_max": prod_data.get("burn_time_max", 40),
                    "wax_type": "100% Natural Soy Wax",
                    "wick_type": "Cotton Wick",
                    "is_active": True,
                    "is_featured": prod_data.get("is_featured", False),
                    "is_bestseller": prod_data.get("is_bestseller", False),
                    "is_new": prod_data.get("is_new", True),
                    "is_gift_ready": prod_data.get("is_gift_ready", True),
                    "ingredients": "100% Natural Soy Wax, Premium Cotton Wick, Fragrance Oil, Natural Botanicals",
                    "care_instructions": "Trim wick to 1/4 inch before each use. Keep away from drafts. Never leave unattended.",
                }
            )
            if created:
                self.stdout.write(f"  + Product: {product.name}")
            if not options["no-images"] and created:
                query = prod_data.get("search_query", "luxury candle")
                image_data = fetch_image(query, unsplash_key, pexels_key)
                if image_data:
                    img = ProductImage(product=product, is_primary=True, alt_text=product.name)
                    img.image.save(f"{uuid.uuid4()}.jpg", ContentFile(image_data), save=True)
                    self.stdout.write(f"    Image saved for: {product.name}")
                else:
                    self.stdout.write(f"    No image for: {product.name} (add API keys to .env)")

        self.stdout.write(self.style.SUCCESS(f"Done! {Product.objects.count()} products imported."))
