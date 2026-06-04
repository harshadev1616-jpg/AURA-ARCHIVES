from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("submit/", views.submit_review, name="submit"),
    path("helpful/", views.mark_helpful, name="helpful"),
]
