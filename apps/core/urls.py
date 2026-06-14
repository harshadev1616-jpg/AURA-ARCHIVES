from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('search/', views.search, name='search'),
    path('newsletter/', views.newsletter_signup, name='newsletter'),
    # One-time admin bootstrap (self-disables once a superuser exists)
    path('setup-admin/', views.setup_admin, name='setup_admin'),
    # PWA
    path('manifest.webmanifest', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('offline/', views.offline, name='offline'),
]
