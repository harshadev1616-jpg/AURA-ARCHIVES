import requests
import uuid
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings

PRODUCT_DATA = [
    {
        "name": "Daisy Glow Set", "category": "Gift Sets",
        "description": "Three little suns in a box. Our Daisy Glow Set gathers three hand-poured soy candles, each one capturing the open-hearted cheer of a daisy field in June — the kind you'd run through as a child, arms wide, certain the summer would never end.",
        "short_description": "A trio of hand-poured daisy candles — bottled sunshine for someone you love.",
        "fragrance_notes": "Fresh Daisy, White Musk, Light Citrus",
        "notes_top": "Sun-warmed citrus zest", "notes_heart": "Fresh daisy & green stem", "notes_base": "Soft white musk",
        "moment": "The first warm morning when the windows finally come open again.",
        "story": "We poured the very first Daisy Glow on a friend's kitchen table, the week she moved into a home of her own. We wanted to gift her light — something small enough to hold, bright enough to fill a room. The set has been our way of saying 'new beginnings' ever since.",
        "ritual": "Light all three at once for a celebration, or one at a time to stretch the joy across three slow weekends.",
        "price": "1299.00", "compare_price": "1599.00", "stock": 25, "burn_time_min": 35, "burn_time_max": 45, "is_featured": True, "is_bestseller": True, "search_query": "candle gift set luxury"},
    {
        "name": "Sunlit Bloom", "category": "Floral",
        "description": "A garden at the golden hour, caught in wax. Sunlit Bloom opens like petals turning to face the late afternoon — warm, unhurried, generous. It is the candle we reach for when we want the room to feel like a long, slow exhale.",
        "short_description": "Warm florals and golden amber — the long exhale at the end of a good day.",
        "fragrance_notes": "Sunflower, Jasmine, Warm Amber, Vanilla",
        "notes_top": "Sunflower & bergamot", "notes_heart": "Jasmine petals", "notes_base": "Warm amber & vanilla",
        "moment": "Golden hour on a Sunday, when there is nowhere else you need to be.",
        "story": "Sunlit Bloom began as an attempt to bottle 6 p.m. in late June — that fleeting half-hour when the light goes amber and everything softens. It took nineteen pours to get the warmth right. We knew we had it when the studio fell quiet and someone simply said, 'oh.'",
        "ritual": "Best lit an hour before guests arrive, so the warmth has time to settle into the corners of the room.",
        "price": "799.00", "compare_price": "999.00", "stock": 40, "burn_time_min": 45, "burn_time_max": 55, "is_featured": True, "is_bestseller": True, "search_query": "floral candle luxury home"},
    {
        "name": "Blush Heart Candle", "category": "Gift Candles",
        "description": "Shaped by hand into a soft blush heart, this little candle says the thing you can't always find words for. Rose and peony bloom over a whisper of pink sugar — tender, romantic, and entirely sincere.",
        "short_description": "A hand-shaped blush heart — for saying the unsayable thing.",
        "fragrance_notes": "Rose, Peony, Pink Sugar, Soft Musk",
        "notes_top": "Pink sugar", "notes_heart": "Rose & peony", "notes_base": "Soft skin musk",
        "moment": "The pause before you say 'I'm glad it's you.'",
        "story": "Every Blush Heart is shaped by hand, which means no two are quite alike — a little lopsided, a little perfect, exactly like the love it's meant to carry. We made the first one for a wedding and haven't stopped since.",
        "ritual": "Gift it unlit, so they get to strike the first match themselves — the start of their own small ritual.",
        "price": "649.00", "compare_price": "849.00", "stock": 30, "burn_time_min": 25, "burn_time_max": 35, "is_featured": True, "is_new": True, "search_query": "pink candle romantic gift"},
    {
        "name": "Lavender Dreams", "category": "Wellness",
        "description": "The deep breath you keep forgetting to take. French lavender drifts over chamomile and clean cotton — a quiet, grounding calm we built for the end of long days and the start of slow mornings.",
        "short_description": "French lavender and chamomile — a candle that lowers your shoulders.",
        "fragrance_notes": "French Lavender, Chamomile, Eucalyptus, Clean Cotton",
        "notes_top": "Cool eucalyptus", "notes_heart": "French lavender", "notes_base": "Chamomile & clean cotton",
        "moment": "9 p.m., phone face-down, the day finally letting go of you.",
        "story": "Lavender Dreams was born out of our own burnout. We wanted a scent that felt like permission — to stop, to rest, to do nothing at all. We tested it during the studio's hardest month, and it's been our nightly full-stop ever since.",
        "ritual": "Light it twenty minutes before bed, dim the lights, and let the room tell your body it's safe to slow down.",
        "price": "599.00", "compare_price": "749.00", "stock": 50, "burn_time_min": 40, "burn_time_max": 50, "is_bestseller": True, "search_query": "lavender candle spa wellness"},
    {
        "name": "Petal Crown Collection", "category": "Floral",
        "description": "A crown of real dried flowers, hand-placed one petal at a time around a soft botanical glow. Part candle, part keepsake — too lovely to rush, made to be lingered over.",
        "short_description": "Hand-placed dried flowers crowning a soft botanical glow.",
        "fragrance_notes": "Wildflower, Rose Hip, Bergamot, Green Tea",
        "notes_top": "Bergamot & green tea", "notes_heart": "Wild meadow flowers", "notes_base": "Rose hip & soft moss",
        "moment": "The afternoon you finally make a corner of your home just for you.",
        "story": "Each crown is built by hand, petal by petal, by our studio florist — roughly forty minutes of quiet, careful work per candle. We pick the blooms ourselves at the start of each season, so the collection is never quite the same twice.",
        "ritual": "Let the flower crown burn down slowly the first time; it releases the botanicals like a garden waking up.",
        "price": "1099.00", "compare_price": "1299.00", "stock": 15, "burn_time_min": 30, "burn_time_max": 40, "is_featured": True, "is_new": True, "search_query": "dried flowers candle aesthetic"},
    {
        "name": "Vanilla Amber Luxe", "category": "Classic",
        "description": "Our most-loved scent, and the easiest to fall for. Madagascar vanilla melts into warm amber and sandalwood — rich, enveloping, and quietly luxurious, like cashmere for a room.",
        "short_description": "Madagascar vanilla and warm amber — cashmere for the room.",
        "fragrance_notes": "Madagascar Vanilla, Warm Amber, Sandalwood, Tonka Bean",
        "notes_top": "Tonka bean", "notes_heart": "Madagascar vanilla", "notes_base": "Warm amber & sandalwood",
        "moment": "Rain against the window, a book, and absolutely nowhere to be.",
        "story": "Vanilla Amber Luxe is the candle that started the whole studio. It was the first scent we ever blended — and the one customers kept coming back for. We've refined the recipe a dozen times, but its heart has never changed.",
        "ritual": "A first-burn candle: give it three full hours so the wax pools to the very edge and the amber blooms.",
        "price": "899.00", "compare_price": "1099.00", "stock": 35, "burn_time_min": 50, "burn_time_max": 60, "is_bestseller": True, "search_query": "vanilla candle luxury warm"},
    {
        "name": "Rose Garden Gift Box", "category": "Gift Sets",
        "description": "Three roses, three moods, one keepsake box. Turkish rose, Bulgarian rose, and a smoky breath of oud — our most lavish gift, made for the people who deserve to be spoiled.",
        "short_description": "A lavish trio of roses in a keepsake box — for spoiling someone properly.",
        "fragrance_notes": "Turkish Rose, Bulgarian Rose, White Jasmine, Oud",
        "notes_top": "Bulgarian rose", "notes_heart": "Turkish rose & jasmine", "notes_base": "Smoky oud",
        "moment": "The anniversary you actually remembered — and went all out for.",
        "story": "We sourced three different roses for this set because no single rose could say everything. Together they tell a fuller story: the bright bloom, the deep velvet centre, and the smoke that lingers after. The box is built to be kept long after the candles are gone.",
        "ritual": "Burn them in order — Bulgarian, then Turkish, then oud — to follow a rose from first light to dusk.",
        "price": "2199.00", "compare_price": "2599.00", "stock": 20, "burn_time_min": 35, "burn_time_max": 45, "is_featured": True, "is_gift_ready": True, "search_query": "rose candle gift box premium"},
    {
        "name": "Midnight Bloom", "category": "Classic",
        "description": "Some flowers only open after dark. Midnight Bloom is night jasmine and black rose over dark amber and cedar — mysterious, a little dramatic, and unforgettable. The candle for the version of you that comes alive at night.",
        "short_description": "Night jasmine and black rose over dark amber — for the after-dark you.",
        "fragrance_notes": "Night Jasmine, Black Rose, Dark Amber, Cedarwood",
        "notes_top": "Black rose", "notes_heart": "Night-blooming jasmine", "notes_base": "Dark amber & cedarwood",
        "moment": "Late, the city quiet, a glass of something good in your hand.",
        "story": "Midnight Bloom came from a single evening — windows open, jasmine drifting in from somewhere we couldn't see, the day's noise finally gone. We chased that scent for months. This is as close as we've come to bottling the dark.",
        "ritual": "Light it after everyone's asleep, when the house is yours again and the night feels wide open.",
        "price": "749.00", "compare_price": "949.00", "stock": 28, "burn_time_min": 40, "burn_time_max": 50, "is_new": True, "search_query": "dark floral candle elegant"},
]

CATEGORY_DATA = [
    {
        "name": "Gift Sets", "sort_order": 1,
        "tagline": "For the people who deserve more than one candle.",
        "description": "Curated candle gift sets for every occasion",
        "story": "Some moments are too big for a single flame. Our gift sets gather two, three, sometimes more candles into one keepsake box — each chosen to tell a fuller story. We design them to be the kind of present that's remembered long after the wax is gone.",
    },
    {
        "name": "Floral", "sort_order": 2,
        "tagline": "A garden you can light.",
        "description": "Beautiful floral-scented soy candles",
        "story": "We grew up around flowers — markets at dawn, gardens after rain, the jasmine that drifts in through an open window at night. The Floral collection is our attempt to keep those blooms alive past their season, pressing whole gardens into soy wax so you can light them whenever you need them.",
    },
    {
        "name": "Gift Candles", "sort_order": 3,
        "tagline": "The thing you say when words won't do.",
        "description": "Perfect candles for gifting",
        "story": "A candle is a quiet kind of love letter. These are the ones we reach for when we want to say 'thinking of you' or 'I'm glad you exist' — hand-shaped, gift-ready, and made to carry a feeling across any distance.",
    },
    {
        "name": "Wellness", "sort_order": 4,
        "tagline": "Permission to slow down.",
        "description": "Calming candles for relaxation and meditation",
        "story": "We built this collection during our own burnout, when we needed a scent that felt like a deep breath. Lavender, chamomile, clean cotton — grounding fragrances designed to lower your shoulders and tell your body the day is finally over.",
    },
    {
        "name": "Classic", "sort_order": 5,
        "tagline": "The ones that started it all.",
        "description": "Our signature classic fragrances",
        "story": "Every studio has its first loves. Vanilla and amber, deep and warm and endlessly comforting — these are the scents we blended at the very beginning, refined over the years but never reinvented. Familiar, dependable, and quietly luxurious.",
    },
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
            # Always (re)apply storytelling so re-runs backfill existing categories
            cat.tagline = cat_data.get("tagline", cat.tagline)
            cat.story = cat_data.get("story", cat.story)
            cat.description = cat_data.get("description", cat.description)
            cat.sort_order = cat_data.get("sort_order", cat.sort_order)
            cat.save(update_fields=["tagline", "story", "description", "sort_order"])
            categories[cat_data["name"]] = cat
            self.stdout.write(f"  {'+' if created else '~'} Category: {cat.name}")

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
                    "notes_top": prod_data.get("notes_top", ""),
                    "notes_heart": prod_data.get("notes_heart", ""),
                    "notes_base": prod_data.get("notes_base", ""),
                    "moment": prod_data.get("moment", ""),
                    "story": prod_data.get("story", ""),
                    "ritual": prod_data.get("ritual", ""),
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
            else:
                # Backfill storytelling onto products created before stories existed
                product.story = prod_data.get("story", product.story)
                product.moment = prod_data.get("moment", product.moment)
                product.ritual = prod_data.get("ritual", product.ritual)
                product.notes_top = prod_data.get("notes_top", product.notes_top)
                product.notes_heart = prod_data.get("notes_heart", product.notes_heart)
                product.notes_base = prod_data.get("notes_base", product.notes_base)
                product.description = prod_data.get("description", product.description)
                product.short_description = prod_data.get("short_description", product.short_description)
                product.save(update_fields=[
                    "story", "moment", "ritual", "notes_top", "notes_heart",
                    "notes_base", "description", "short_description",
                ])
                self.stdout.write(f"  ~ Updated story: {product.name}")
            if not options["no_images"] and created:
                query = prod_data.get("search_query", "luxury candle")
                image_data = fetch_image(query, unsplash_key, pexels_key)
                if image_data:
                    img = ProductImage(product=product, is_primary=True, alt_text=product.name)
                    img.image.save(f"{uuid.uuid4()}.jpg", ContentFile(image_data), save=True)
                    self.stdout.write(f"    Image saved for: {product.name}")
                else:
                    self.stdout.write(f"    No image for: {product.name} (add API keys to .env)")

        self.stdout.write(self.style.SUCCESS(f"Done! {Product.objects.count()} products imported."))
