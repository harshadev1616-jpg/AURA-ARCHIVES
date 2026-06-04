from django.test import TestCase, Client
from apps.accounts.models import User, Address


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email="a@b.com", password="pass123", first_name="John", last_name="Doe")
        self.assertEqual(user.email, "a@b.com")
        self.assertEqual(user.get_full_name(), "John Doe")
        self.assertTrue(user.check_password("pass123"))

    def test_create_superuser(self):
        admin = User.objects.create_superuser(email="admin@b.com", password="pass123", first_name="Admin", last_name="User")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class AddressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@b.com", password="pass123", first_name="U", last_name="V")

    def test_default_address_unique(self):
        a1 = Address.objects.create(user=self.user, full_name="A", phone="1", address_line1="L1",
                                    city="C", state="S", pincode="123456", is_default=True)
        a2 = Address.objects.create(user=self.user, full_name="B", phone="2", address_line1="L2",
                                    city="C", state="S", pincode="123456", is_default=True)
        a1.refresh_from_db()
        self.assertFalse(a1.is_default)
        self.assertTrue(a2.is_default)


class AuthViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_page(self):
        resp = self.client.get("/accounts/register/")
        self.assertEqual(resp.status_code, 200)

    def test_login_page(self):
        resp = self.client.get("/accounts/login/")
        self.assertEqual(resp.status_code, 200)


class AccountPagesRenderTests(TestCase):
    """Every logged-in account page should render (regression for unrouted views)."""
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email="pages@b.com", password="pass12345", first_name="Pg", last_name="User")
        self.client.force_login(self.user)

    def test_all_account_pages_load(self):
        for path in ["/accounts/dashboard/", "/accounts/profile/", "/accounts/addresses/",
                     "/accounts/addresses/add/", "/accounts/wishlist/", "/accounts/notifications/"]:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, f"{path} returned {resp.status_code}")
