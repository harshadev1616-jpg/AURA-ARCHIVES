from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('quiz/', views.scent_quiz, name='quiz'),
    path('quiz/result/', views.scent_quiz_result, name='quiz_result'),
    path('quick-view/<slug:slug>/', views.quick_view, name='quick_view'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='detail'),
    path('notify-restock/', views.notify_back_in_stock, name='notify_restock'),
    path('cart/add/', views.add_to_cart, name='cart_add'),
    path('cart/update/', views.update_cart, name='cart_update'),
    path('cart/remove/', views.remove_from_cart, name='cart_remove'),
]
