import json
from decimal import Decimal
from django.test import TestCase, Client
from apps.accounts.models import User
from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem
from apps.coupons.models import Coupon


class CartTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Classic")
        self.product = Product.objects.create(name="Vanilla", category=self.category, price=Decimal("899"), stock=10)

    def test_add_to_cart(self):
        resp = self.client.post("/shop/cart/add/", data={"product_id": self.product.pk, "quantity": 2},
                                content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertEqual(resp.json()["cart_count"], 2)


class CouponTests(TestCase):
    def test_percentage_coupon(self):
        coupon = Coupon.objects.create(code="SAVE10", discount_type="percentage", discount_value=10, min_order_amount=100)
        valid, _ = coupon.is_valid()
        self.assertTrue(valid)
        self.assertEqual(coupon.calculate_discount(Decimal("1000")), Decimal("100"))

    def test_fixed_coupon(self):
        coupon = Coupon.objects.create(code="FLAT50", discount_type="fixed", discount_value=50)
        self.assertEqual(coupon.calculate_discount(Decimal("500")), Decimal("50"))


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@aura.com", password="testpass123", first_name="Test", last_name="User")

    def test_order_number_generated(self):
        order = Order.objects.create(user=self.user, shipping_full_name="Test", shipping_phone="123",
                                     shipping_address_line1="St", shipping_city="City", shipping_state="State", shipping_pincode="123456")
        self.assertTrue(order.order_number.startswith("AA"))

    def test_can_cancel(self):
        order = Order.objects.create(user=self.user, status="pending", shipping_full_name="T", shipping_phone="1",
                                     shipping_address_line1="S", shipping_city="C", shipping_state="St", shipping_pincode="123456")
        self.assertTrue(order.can_cancel())
        order.status = "shipped"
        self.assertFalse(order.can_cancel())


class CheckoutMoneyAndRollbackTests(TestCase):
    """Regression tests for bugs found during stress-testing."""
    def setUp(self):
        from apps.accounts.models import Address
        from apps.products.models import Category, Product
        self.client = Client()
        self.user = User.objects.create_user(email="checkout@test.com", password="pass12345", first_name="Co", last_name="Test")
        self.user.loyalty_points = 200
        self.user.save()
        self.client.force_login(self.user)
        self.addr = Address.objects.create(user=self.user, full_name="Co Test", phone="9", address_line1="1", city="C", state="S", pincode="400001")
        cat = Category.objects.create(name="Test")
        self.product = Product.objects.create(name="Test Candle", category=cat, price=Decimal("1000"), stock=50)

    def _add_to_cart(self, qty=1):
        self.client.post("/shop/cart/add/", data=json.dumps({"product_id": self.product.pk, "quantity": qty}),
                         content_type="application/json")

    def test_redeem_points_at_cod_checkout_does_not_500(self):
        """Regression: request.user is a lazy object — redeem_points must not crash."""
        self._add_to_cart(1)
        resp = self.client.post("/orders/create/", data=json.dumps({
            "address_id": self.addr.pk, "payment_method": "cod", "redeem_points": 200,
        }), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.user.refresh_from_db()
        self.assertEqual(self.user.loyalty_points, 0)  # 200 redeemed
        order = Order.objects.get(pk=resp.json()["order_id"])
        self.assertEqual(order.total, Decimal("800.00"))  # 1000 - 200 points
        self.assertGreaterEqual(order.total, 0)

    def test_razorpay_failure_refunds_points_and_no_dangling_order(self):
        """Regression: failed payment must roll back redeemed points and leave no order."""
        from django.test import override_settings
        self._add_to_cart(1)
        with override_settings(RAZORPAY_KEY_ID="", RAZORPAY_KEY_SECRET=""):
            resp = self.client.post("/orders/create/", data=json.dumps({
                "address_id": self.addr.pk, "payment_method": "razorpay", "redeem_points": 200,
            }), content_type="application/json")
        self.assertFalse(resp.json()["success"])
        self.user.refresh_from_db()
        self.assertEqual(self.user.loyalty_points, 200)  # refunded
        self.assertFalse(Order.objects.filter(user=self.user).exists())  # rolled back


class InventoryTests(TestCase):
    """Stock validation, deduction on purchase, and restock on cancel."""
    def setUp(self):
        from apps.accounts.models import Address
        from apps.products.models import Category, Product
        self.client = Client()
        self.user = User.objects.create_user(email="stock@test.com", password="pass12345", first_name="St", last_name="K")
        self.client.force_login(self.user)
        self.addr = Address.objects.create(user=self.user, full_name="St K", phone="9", address_line1="1", city="C", state="S", pincode="400001")
        cat = Category.objects.create(name="StockCat")
        self.p = Product.objects.create(name="Limited Candle", category=cat, price=Decimal("500"), stock=3, track_inventory=True)

    def _add(self, qty):
        return self.client.post("/shop/cart/add/", data=json.dumps({"product_id": self.p.pk, "quantity": qty}),
                                content_type="application/json").json()

    def test_cannot_add_more_than_stock(self):
        self.assertTrue(self._add(2)["success"])
        self.assertFalse(self._add(2)["success"])   # 2+2 > 3
        self.assertTrue(self._add(1)["success"])     # 2+1 = 3

    def test_checkout_deducts_and_cancel_restores(self):
        self._add(3)
        resp = self.client.post("/orders/create/", data=json.dumps({"address_id": self.addr.pk, "payment_method": "cod"}),
                                content_type="application/json").json()
        self.assertTrue(resp["success"])
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 0)            # deducted
        # out of stock now
        self.assertFalse(self._add(1)["success"])
        # cancel restores
        order = Order.objects.get(pk=resp["order_id"])
        order.status = "cancelled"; order.save()
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 3)            # restored

    def test_stock_never_negative_and_no_double_deduct(self):
        order = Order.objects.create(user=self.user, status="pending", subtotal=Decimal("500"), total=Decimal("500"),
            shipping_full_name="St", shipping_phone="9", shipping_address_line1="1", shipping_city="C", shipping_state="S", shipping_pincode="400001")
        OrderItem.objects.create(order=order, product=self.p, product_name=self.p.name, price=Decimal("500"), quantity=5)
        order.status = "confirmed"; order.save()
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 0)            # clamped, not -2
        order.status = "processing"; order.save()    # committed->committed
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 0)            # no extra deduction


class ReturnsRefundTests(TestCase):
    """Customer return requests + admin approve/reject (refund, restock, notify)."""
    def setUp(self):
        from apps.accounts.models import Address
        from apps.products.models import Category, Product
        self.client = Client()
        self.user = User.objects.create_user(email="ret@test.com", password="pass12345", first_name="Re", last_name="T")
        self.admin = User.objects.create_superuser(email="retadmin@test.com", password="pass12345", first_name="A", last_name="D")
        self.client.force_login(self.user)
        cat = Category.objects.create(name="RetCat")
        self.p = Product.objects.create(name="Ret Candle", category=cat, price=Decimal("500"), stock=10, track_inventory=True)

    def _delivered_order(self, qty=2):
        o = Order.objects.create(user=self.user, status="pending", payment_status="paid",
            subtotal=Decimal("1000"), total=Decimal("1000"), shipping_full_name="Re T", shipping_phone="9",
            shipping_address_line1="1", shipping_city="C", shipping_state="S", shipping_pincode="400001")
        OrderItem.objects.create(order=o, product=self.p, product_name=self.p.name, price=Decimal("500"), quantity=qty)
        o.status = "delivered"; o.save()   # deducts stock
        return o

    def test_only_delivered_orders_can_be_returned(self):
        o = Order.objects.create(user=self.user, status="confirmed", shipping_full_name="x", shipping_phone="9",
            shipping_address_line1="1", shipping_city="C", shipping_state="S", shipping_pincode="400001")
        resp = self.client.post(f"/orders/{o.pk}/return/", data=json.dumps({"reason": "defective", "description": "x"}),
                                content_type="application/json").json()
        self.assertFalse(resp["success"])

    def test_request_then_admin_approve_refunds_and_restocks(self):
        from apps.orders.models import ReturnRequest
        from apps.orders.admin import ReturnRequestAdmin
        from django.contrib.admin.sites import site
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        o = self._delivered_order(qty=2)
        self.p.refresh_from_db(); stock_after_sale = self.p.stock
        resp = self.client.post(f"/orders/{o.pk}/return/", data=json.dumps({"reason": "defective", "description": "cracked"}),
                                content_type="application/json").json()
        self.assertTrue(resp["success"])
        o.refresh_from_db(); self.assertEqual(o.status, "refund_requested")
        rr = ReturnRequest.objects.get(order=o)
        # admin approves
        rf = RequestFactory(); req = rf.post("/"); req.user = self.admin
        req.session = {}; req._messages = FallbackStorage(req)
        ReturnRequestAdmin(ReturnRequest, site).approve_and_refund(req, ReturnRequest.objects.filter(pk=rr.pk))
        rr.refresh_from_db(); o.refresh_from_db(); self.p.refresh_from_db()
        self.assertEqual(rr.status, "approved")
        self.assertEqual(o.payment_status, "refunded")
        self.assertEqual(o.status, "returned")
        self.assertEqual(self.p.stock, stock_after_sale + 2)   # restocked

    def test_duplicate_return_blocked(self):
        o = self._delivered_order()
        self.client.post(f"/orders/{o.pk}/return/", data=json.dumps({"reason": "defective", "description": "a"}), content_type="application/json")
        resp2 = self.client.post(f"/orders/{o.pk}/return/", data=json.dumps({"reason": "defective", "description": "b"}), content_type="application/json").json()
        self.assertFalse(resp2["success"])


class BulkAdminActionTests(TestCase):
    """Bulk status actions fire per-order signals; no-items orders don't phantom-flag stock."""
    def setUp(self):
        from apps.products.models import Category, Product
        self.admin = User.objects.create_superuser(email="bulkadmin@test.com", password="p12345", first_name="A", last_name="D")
        self.buyer = User.objects.create_user(email="bulkbuyer@test.com", password="p12345", first_name="B", last_name="Y")
        cat = Category.objects.create(name="BulkCat")
        self.p = Product.objects.create(name="Bulk Candle", category=cat, price=Decimal("500"), stock=10, track_inventory=True)
        self.client = Client(); self.client.force_login(self.admin)

    def _order(self, status="confirmed"):
        o = Order.objects.create(user=self.buyer, status="pending", payment_status="paid",
            subtotal=Decimal("500"), total=Decimal("500"), shipping_full_name="B", shipping_phone="9",
            shipping_address_line1="1", shipping_city="C", shipping_state="S", shipping_pincode="400001")
        OrderItem.objects.create(order=o, product=self.p, product_name=self.p.name, price=Decimal("500"), quantity=1)
        o.status = status; o.save()  # items exist before confirm -> deducts
        return o

    def test_bulk_mark_shipped_changes_status(self):
        o1, o2 = self._order(), self._order()
        self.client.post("/aura-admin/orders/order/",
                         {"action": "mark_shipped", "_selected_action": [str(o1.pk), str(o2.pk)]})
        o1.refresh_from_db(); o2.refresh_from_db()
        self.assertEqual(o1.status, "shipped"); self.assertEqual(o2.status, "shipped")

    def test_bulk_cancel_restocks_correctly(self):
        o = self._order()
        self.p.refresh_from_db(); self.assertEqual(self.p.stock, 9)  # 1 deducted
        self.client.post("/aura-admin/orders/order/", {"action": "mark_cancelled", "_selected_action": [str(o.pk)]})
        self.p.refresh_from_db(); self.assertEqual(self.p.stock, 10)  # restored exactly, no phantom

    def test_confirmed_order_with_no_items_does_not_flag_stock(self):
        from apps.orders.inventory import deduct_for_order
        o = Order.objects.create(user=self.buyer, status="confirmed", subtotal=0, total=0,
            shipping_full_name="B", shipping_phone="9", shipping_address_line1="1",
            shipping_city="C", shipping_state="S", shipping_pincode="400001")
        o.refresh_from_db()
        self.assertFalse(o.stock_deducted)  # no items -> not flagged


class FulfilmentToolsTests(TestCase):
    """Ship-with-tracking intermediate action + packing-slip PDF."""
    def setUp(self):
        from apps.products.models import Category, Product
        self.admin = User.objects.create_superuser(email="fadmin@test.com", password="p12345", first_name="A", last_name="D")
        self.buyer = User.objects.create_user(email="fbuyer@test.com", password="p12345", first_name="F", last_name="B")
        cat = Category.objects.create(name="FCat")
        self.p = Product.objects.create(name="F Candle", category=cat, price=Decimal("500"), stock=10)
        self.o = Order.objects.create(user=self.buyer, status="confirmed", payment_status="paid",
            subtotal=Decimal("500"), total=Decimal("500"), shipping_full_name="F B", shipping_phone="9",
            shipping_address_line1="1", shipping_city="C", shipping_state="S", shipping_pincode="400001")
        OrderItem.objects.create(order=self.o, product=self.p, product_name=self.p.name, price=Decimal("500"), quantity=2)
        self.client = Client(); self.client.force_login(self.admin)

    def test_ship_with_tracking_form_then_apply(self):
        # intermediate form renders
        r = self.client.post("/aura-admin/orders/order/", {"action": "ship_with_tracking", "_selected_action": [str(self.o.pk)]})
        self.assertEqual(r.status_code, 200)
        self.assertIn(f"tracking_{self.o.pk}", r.content.decode())
        # apply
        self.client.post("/aura-admin/orders/order/", {
            "action": "ship_with_tracking", "_selected_action": [str(self.o.pk)],
            "apply": "1", f"tracking_{self.o.pk}": "TRK123", "courier_name": "Bluedart",
        })
        self.o.refresh_from_db()
        self.assertEqual(self.o.status, "shipped")
        self.assertEqual(self.o.tracking_number, "TRK123")
        self.assertEqual(self.o.courier_name, "Bluedart")

    def test_packing_slip_pdf(self):
        r = self.client.post("/aura-admin/orders/order/", {"action": "packing_slips", "_selected_action": [str(self.o.pk)]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))


class CartDrawerTests(TestCase):
    def setUp(self):
        from apps.products.models import Category, Product
        self.client = Client()
        cat = Category.objects.create(name="DrawCat")
        self.p = Product.objects.create(name="Drawer Candle", category=cat, price=Decimal("800"), stock=10)

    def test_drawer_empty(self):
        r = self.client.get("/orders/cart/drawer/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Your bag is empty", r.content.decode())

    def test_drawer_with_item(self):
        self.client.post("/shop/cart/add/", data=json.dumps({"product_id": self.p.pk, "quantity": 2}),
                         content_type="application/json")
        r = self.client.get("/orders/cart/drawer/")
        html = r.content.decode()
        self.assertIn("Drawer Candle", html)
        self.assertIn("Checkout", html)
        self.assertIn("View full bag", html)
