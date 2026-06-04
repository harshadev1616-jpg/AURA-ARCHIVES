from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from apps.seo.sitemaps import (
    ProductSitemap, CategorySitemap, BlogSitemap, StaticViewSitemap
)
from apps.seo import views as seo_views

sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'blog': BlogSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('aura-admin/', admin.site.urls),
    path('insights/', include('apps.analytics.urls')),
    path('', include('apps.core.urls')),
    path('shop/', include('apps.products.urls')),
    path('orders/', include('apps.orders.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('wishlist/', include('apps.wishlist.urls')),
    path('coupons/', include('apps.coupons.urls')),
    path('blog/', include('apps.blog.urls')),
    path('pages/', include('apps.cms.urls')),
    path('seo/', include('apps.seo.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', seo_views.robots_txt, name='robots_txt'),
]

admin.site.site_header = 'Aura Archives Admin'
admin.site.site_title = 'Aura Archives'
admin.site.index_title = 'Welcome to Aura Archives Admin'
admin.site.index_template = 'admin/aura_index.html'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

# Serve media files in all environments (WhiteNoise handles static, Django serves media)
from django.views.static import serve as _serve
urlpatterns += [
    path('media/<path:path>', _serve, {'document_root': settings.MEDIA_ROOT}),
]
