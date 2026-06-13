from django.urls import path
from . import views
app_name = "orders"
urlpatterns = [
    path("cart/", views.cart_view, name="cart"),
    path("cart/drawer/", views.cart_drawer, name="cart_drawer"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("create/", views.create_order, name="create"),
    path("verify-payment/", views.verify_payment, name="verify_payment"),
    path("apply-coupon/", views.apply_coupon, name="apply_coupon"),
    path("", views.order_list, name="list"),
    path("<int:pk>/", views.order_detail, name="detail"),
    path("<int:pk>/invoice/", views.order_invoice, name="invoice"),
    path("<int:pk>/label/", views.order_shipping_label, name="shipping_label"),
    path("<int:pk>/cancel/", views.cancel_order, name="cancel"),
    path("<int:pk>/return/", views.request_return, name="request_return"),
]
