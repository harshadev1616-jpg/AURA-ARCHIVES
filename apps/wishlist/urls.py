from django.urls import path
from . import views
app_name = "wishlist"
urlpatterns = [path("toggle/", views.toggle_wishlist, name="toggle"), path("", views.wishlist_view, name="list")]
