from django.urls import path
from . import views
app_name = "accounts"
urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("addresses/", views.address_list, name="addresses"),
    path("addresses/add/", views.address_add, name="address_add"),
    path("addresses/<int:pk>/edit/", views.address_edit, name="address_edit"),
    path("addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("notifications/", views.notifications, name="notifications"),
]
