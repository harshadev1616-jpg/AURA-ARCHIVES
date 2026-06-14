from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count
import json
from apps.products.models import Product, Category
from apps.cms.models import Banner, Announcement
from apps.blog.models import BlogPost
from apps.reviews.models import Review
from apps.accounts.models import User


def home(request):
    featured_products = Product.objects.filter(is_active=True, is_featured=True).prefetch_related('images')[:8]
    bestsellers = Product.objects.filter(is_active=True, is_bestseller=True).prefetch_related('images')[:6]
    new_arrivals = Product.objects.filter(is_active=True, is_new=True).prefetch_related('images')[:4]
    categories = Category.objects.filter(is_active=True, parent=None).order_by('sort_order')[:6]
    hero_banners = Banner.objects.filter(is_active=True, position='hero').order_by('sort_order')
    featured_banners = Banner.objects.filter(is_active=True, position='home_featured').order_by('sort_order')[:4]
    reviews = Review.objects.filter(is_approved=True).select_related('user', 'product').order_by('-helpful_count')[:6]
    blog_posts = BlogPost.objects.filter(status='published').order_by('-published_at')[:3]
    insta_products = Product.objects.filter(is_active=True, images__isnull=False).distinct().prefetch_related('images')[:6]
    context = {
        'featured_products': featured_products,
        'bestsellers': bestsellers,
        'new_arrivals': new_arrivals,
        'categories': categories,
        'hero_banners': hero_banners,
        'featured_banners': featured_banners,
        'reviews': reviews,
        'blog_posts': blog_posts,
        'insta_products': insta_products,
    }
    return render(request, 'home/index.html', context)


def about(request):
    return render(request, 'home/about.html')


def contact(request):
    if request.method == 'POST':
        # Handle contact form
        return JsonResponse({'success': True, 'message': 'Thank you! We will get back to you soon.'})
    return render(request, 'home/contact.html')


def search(request):
    q = request.GET.get('q', '')
    products = []
    if q:
        from django.db.models import Q
        products = Product.objects.filter(
            is_active=True
        ).filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(fragrance_notes__icontains=q)
        ).prefetch_related('images')[:20]
    return render(request, 'products/search.html', {'products': products, 'query': q})


@require_POST
def newsletter_signup(request):
    data = json.loads(request.body)
    email = data.get('email', '')
    if email:
        try:
            user = User.objects.get(email=email)
            user.newsletter_subscribed = True
            user.save(update_fields=['newsletter_subscribed'])
        except User.DoesNotExist:
            pass
        return JsonResponse({'success': True, 'message': 'Thank you for subscribing!'})
    return JsonResponse({'success': False, 'message': 'Please provide a valid email'})


# ============================================================
#  PWA — manifest, service worker, offline fallback
# ============================================================
from django.http import HttpResponse
from django.templatetags.static import static as static_url


def offline(request):
    return render(request, 'offline.html')


def manifest(request):
    icon = static_url('images/icon-512.png')
    data = {
        "name": "Aura Archives",
        "short_name": "Aura",
        "description": "Handmade luxury soy candles — Light That Preserves Moments.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#F8F4EF",
        "theme_color": "#C9A86A",
        "orientation": "portrait-primary",
        "categories": ["shopping", "lifestyle"],
        "icons": [
            {"src": static_url('images/icon-192.png'), "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": icon, "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
        "shortcuts": [
            {"name": "Shop Candles", "url": "/shop/"},
            {"name": "Find Your Scent", "url": "/shop/quiz/"},
            {"name": "My Orders", "url": "/orders/"},
        ],
    }
    return JsonResponse(data, content_type='application/manifest+json')


def service_worker(request):
    sw = """
const CACHE = 'aura-v1';
const PRECACHE = ['/', '/offline/', '/static/css/main.css', '/static/js/main.js'];

self.addEventListener('install', (e) => {
    e.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (e) => {
    const req = e.request;
    if (req.method !== 'GET') return;
    const url = new URL(req.url);
    // Never cache admin or auth-sensitive paths
    if (url.pathname.startsWith('/aura-admin') || url.pathname.startsWith('/accounts') || url.pathname.startsWith('/orders')) return;

    if (req.mode === 'navigate') {
        // Network-first for pages, fall back to cache then offline page
        e.respondWith(
            fetch(req).then((res) => {
                const copy = res.clone();
                caches.open(CACHE).then((c) => c.put(req, copy));
                return res;
            }).catch(() => caches.match(req).then((r) => r || caches.match('/offline/')))
        );
        return;
    }
    // Cache-first for static assets
    if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
        e.respondWith(
            caches.match(req).then((cached) => cached || fetch(req).then((res) => {
                const copy = res.clone();
                caches.open(CACHE).then((c) => c.put(req, copy));
                return res;
            }))
        );
    }
});
"""
    return HttpResponse(sw, content_type='application/javascript')


@csrf_exempt
def setup_admin(request):
    """Bootstrap or repair the admin superuser.

    Two modes:

    * **Bootstrap** — when no superuser exists yet, anyone may create the first
      one, then the page locks itself.
    * **Repair** — once a superuser exists the page is locked, *unless* the
      request carries a ``token`` that matches the ``SETUP_ADMIN_TOKEN`` env var.
      With a valid token you can reset an admin's email/password and force the
      ``is_staff`` / ``is_superuser`` / ``is_active`` flags — the fix for
      "enter a correct email and password for a staff account" when the stored
      password isn't what you think it is. Unset SETUP_ADMIN_TOKEN once you're
      back in.

    No secrets live in code; the repair token comes from the environment.
    """
    import os
    import hmac
    from django.contrib.auth import get_user_model
    from django.http import HttpResponse, HttpResponseForbidden
    from django.utils.html import escape

    User = get_user_model()
    admin_exists = User.objects.filter(is_superuser=True).exists()

    token_env = (os.environ.get("SETUP_ADMIN_TOKEN") or "").strip()
    supplied = (request.GET.get("token") or request.POST.get("token") or "").strip()
    token_ok = bool(token_env) and hmac.compare_digest(token_env, supplied)

    # Locked once an admin exists — only a valid repair token reopens it.
    if admin_exists and not token_ok:
        return HttpResponseForbidden(
            "An admin already exists — this setup page is locked. "
            "To reset the admin login, set a SETUP_ADMIN_TOKEN env var on the "
            "deployment and visit this page with ?token=<that value>."
        )

    repair = admin_exists  # an admin already existed → we're resetting, not creating
    verb = "Reset" if repair else "Create"
    token_field = (
        f"<input type='hidden' name='token' value='{escape(supplied)}'>" if repair else ""
    )

    msg = ""
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        password = (request.POST.get("password") or "").strip()
        if not email or not password:
            msg = "Please enter both an email and a password."
        else:
            user, _ = User.objects.get_or_create(email=email, defaults={"is_active": True})
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.set_password(password)
            user.save()
            note = (
                "This setup page is now disabled."
                if not repair
                else "Remove the SETUP_ADMIN_TOKEN env var to re-lock this page."
            )
            return HttpResponse(
                "<div style='font-family:sans-serif;max-width:480px;margin:12vh auto;text-align:center'>"
                f"<h2>&#10003; Admin {verb.lower()}</h2>"
                f"<p>Account <b>{escape(email)}</b> is ready (staff + superuser, active).</p>"
                "<p><a href='/aura-admin/' style='display:inline-block;padding:11px 22px;background:#2B2B2B;"
                "color:#fff;text-decoration:none;border-radius:999px'>Log in to the admin &rarr;</a></p>"
                f"<p style='color:#999;font-size:13px'>{note}</p></div>"
            )

    intro = (
        "One-time setup. Create your admin login, then this page locks itself."
        if not repair
        else "Repair mode (valid token). Re-set the admin email + password below; "
        "the staff/superuser/active flags are forced on."
    )
    return HttpResponse(
        "<div style='font-family:sans-serif;max-width:420px;margin:10vh auto;padding:0 16px'>"
        f"<h2 style='font-family:Georgia,serif'>Aura Archives &mdash; {verb.lower()} admin</h2>"
        f"<p style='color:#666'>{intro}</p>"
        f"<p style='color:#b4453a'>{escape(msg)}</p>"
        "<form method='post' style='display:grid;gap:14px'>"
        f"{token_field}"
        "<label>Email<br><input name='email' type='email' required "
        "style='width:100%;box-sizing:border-box;padding:11px;border:1px solid #ccc;border-radius:8px'></label>"
        "<label>Password<br><input name='password' type='password' required "
        "style='width:100%;box-sizing:border-box;padding:11px;border:1px solid #ccc;border-radius:8px'></label>"
        f"<button style='padding:13px;background:#B8945A;color:#fff;border:0;border-radius:999px;"
        f"cursor:pointer;font-size:15px'>{verb} admin</button>"
        "</form></div>"
    )


@csrf_exempt
def diag_9f3k(request):
    """TEMPORARY diagnostics — surfaces the real storefront 500 cause without
    enabling DEBUG. Reports DB connectivity, applied-migration count, table
    presence, and a traceback for the first failing query. Remove after use."""
    import traceback as _tb
    from django.http import HttpResponse
    from django.db import connection
    out = []

    def check(label, fn):
        try:
            out.append(f"[OK]  {label}: {fn()}")
        except Exception:
            out.append(f"[ERR] {label}:\n{_tb.format_exc()}")

    check("db connection", lambda: (connection.ensure_connection() or "connected"))
    check("migrations applied", lambda: _count_rows(connection, "django_migrations"))
    check("Product.count", lambda: Product.objects.count())
    check("Category.count", lambda: Category.objects.count())
    check("Banner.count", lambda: Banner.objects.count())
    check("Announcement.count", lambda: Announcement.objects.count())
    check("BlogPost.count", lambda: BlogPost.objects.count())
    check("Review.count", lambda: Review.objects.count())
    check("User.count", lambda: User.objects.count())
    check("tables present", lambda: _list_tables(connection))
    check("render home view", _render_home)
    return HttpResponse("\n\n".join(out), content_type="text/plain")


def _render_home():
    from django.test import Client
    c = Client(raise_request_exception=True)
    resp = c.get("/", HTTP_HOST="aura-archives.vercel.app", secure=True)
    return f"status={resp.status_code}"


def _count_rows(connection, table):
    with connection.cursor() as c:
        c.execute(f"SELECT count(*) FROM {table}")
        return c.fetchone()[0]


def _list_tables(connection):
    with connection.cursor() as c:
        c.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        )
        return ", ".join(r[0] for r in c.fetchall())
