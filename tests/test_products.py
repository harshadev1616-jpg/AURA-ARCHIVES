from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from apps.products.models import Product, Category


class ProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Floral")
        self.product = Product.objects.create(
            name="Sunlit Bloom", category=self.category,
            price=Decimal("799.00"), compare_price=Decimal("999.00"), stock=10,
        )

    def test_slug_auto_generated(self):
        self.assertEqual(self.product.slug, "sunlit-bloom")

    def test_sku_auto_generated(self):
        self.assertTrue(self.product.sku.startswith("AA-"))

    def test_discount_percentage(self):
        self.assertEqual(self.product.discount_percentage, 20)

    def test_is_in_stock(self):
        self.assertTrue(self.product.is_in_stock)
        self.product.stock = 0
        self.assertFalse(self.product.is_in_stock)

    def test_is_low_stock(self):
        self.product.stock = 3
        self.product.low_stock_threshold = 5
        self.assertTrue(self.product.is_low_stock)

    def test_category_product_count(self):
        self.assertEqual(self.category.product_count, 1)


class ProductViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Gift Sets")
        self.product = Product.objects.create(name="Daisy Glow", category=self.category, price=Decimal("1299"), stock=5)

    def test_product_list_view(self):
        resp = self.client.get(reverse("products:list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Daisy Glow")

    def test_product_detail_view(self):
        resp = self.client.get(self.product.get_absolute_url())
        self.assertEqual(resp.status_code, 200)

    def test_search(self):
        resp = self.client.get(reverse("search") + "?q=daisy")
        self.assertEqual(resp.status_code, 200)


class ScentQuizTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Wellness")
        self.calm = Product.objects.create(
            name="Lavender Calm", category=self.category, price=Decimal("599"), stock=10,
            fragrance_notes="French Lavender, Chamomile", notes_heart="French lavender",
            moment="9pm, phone down", is_bestseller=True,
        )
        self.bold = Product.objects.create(
            name="Dark Night", category=Category.objects.create(name="Classic"),
            price=Decimal("749"), stock=10, fragrance_notes="Oud, Black Rose, Cedar",
            notes_base="Dark amber & cedarwood",
        )

    def test_quiz_page_loads(self):
        resp = self.client.get(reverse("products:quiz"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Find Your Moment")

    def test_quiz_matches_calm_to_wellness(self):
        import json
        resp = self.client.post(
            reverse("products:quiz_result"),
            data=json.dumps({"answers": {"feeling": "calm", "time": "anytime", "note": "herbal", "who": "me"}}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["match"]["name"], "Lavender Calm")

    def test_quiz_matches_bold_to_woody(self):
        import json
        resp = self.client.post(
            reverse("products:quiz_result"),
            data=json.dumps({"answers": {"feeling": "bold", "time": "night", "note": "woody", "who": "me"}}),
            content_type="application/json",
        )
        self.assertEqual(resp.json()["match"]["name"], "Dark Night")


class QuickViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        cat = Category.objects.create(name="QV")
        self.product = Product.objects.create(name="QuickLook Candle", category=cat, price=Decimal("799"),
                                              compare_price=Decimal("999"), stock=5, moment="A quiet evening")

    def test_quick_view_returns_partial(self):
        resp = self.client.get(reverse("products:quick_view", kwargs={"slug": self.product.slug}))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("QuickLook Candle", html)
        self.assertIn("Add to Cart", html)
        self.assertIn("View full details", html)

    def test_quick_view_404_for_unknown(self):
        resp = self.client.get(reverse("products:quick_view", kwargs={"slug": "nope-nope"}))
        self.assertEqual(resp.status_code, 404)
