# 🕯️ Aura Archives

**Light That Preserves Moments**

A complete, production-ready e-commerce platform for a premium handmade candle brand, built with Django 5, Tailwind CSS, PostgreSQL, and Razorpay payments.

---

## ✨ Features

### Storefront
- **Luxury Home Page** — hero, featured collections, bestsellers, reviews, newsletter
- **Full Shop** — categories, variants, multi-image galleries, search, filters, sorting
- **Product Pages** — gallery with zoom, fragrance notes, burn time, ingredients, reviews
- **Cart & Checkout** — session cart, coupons, address management, Razorpay + COD
- **Order Tracking** — status timeline, tracking numbers, history
- **User Accounts** — register, login, dashboard, profile, address book, wishlist, orders, notifications
- **Dark / Light Mode** — persisted in localStorage
- **WhatsApp Chat** — floating contact button
- **Mobile-First Responsive** design

### Admin & CMS
- **Custom Analytics Dashboard** — revenue, orders, customers, low-stock alerts
- **Product Management** — variants, images, inventory, bulk import/export
- **Order Management** — status changes, tracking, refunds, returns
- **Coupon Management** — percentage / fixed / free-shipping
- **CMS** — pages, banners, announcements, popups (no code needed)
- **Blog Management**, **Review Moderation**, **Site / SEO / Shipping settings**

### SEO
Meta tags, Open Graph, sitemap.xml, robots.txt, canonical URLs.

### Images
`import_aura_images` management command fetches royalty-free candle imagery from Unsplash / Pexels and populates demo products.

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5 |
| Frontend | Django Templates + Tailwind CSS + Alpine.js |
| Database | PostgreSQL (SQLite fallback for dev) |
| Payments | Razorpay |
| Media | Local (dev) / AWS S3-ready (prod) |
| Cache | Redis |
| Auth | Django Auth + django-allauth |

---

## 📁 Project Structure

```
aura_archives/
├── aura_archives/           # Project config
│   ├── settings/            # base / development / production
│   ├── urls.py · wsgi.py · asgi.py
├── apps/
│   ├── core/                # Site settings, home, base models, mgmt commands
│   ├── products/            # Catalog, categories, variants, images
│   ├── orders/              # Cart, checkout, Razorpay, returns
│   ├── accounts/            # Custom User, addresses, dashboard
│   ├── reviews/  wishlist/  coupons/
│   ├── blog/  cms/  seo/    # Content & marketing
│   ├── analytics/  notifications/  shipping/
├── templates/               # All HTML (base, components, pages)
├── static/                  # css / js / images
├── tests/                   # Unit tests
├── requirements.txt · Dockerfile · docker-compose.yml
```

---

## 🚀 Quick Start (Local)

### 1. Clone & create a virtualenv
```bash
cd aura_archives
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env — set SECRET_KEY, DATABASE_URL, RAZORPAY keys, UNSPLASH/PEXELS keys
```
> No PostgreSQL handy? Leave `DATABASE_URL` unset and it falls back to SQLite.

### 4. Migrate & create admin
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Seed demo content & products
```bash
python manage.py seed_data            # settings, pages, coupons, shipping
python manage.py import_aura_images   # demo products + collections + stories + images
python manage.py seed_journal         # The Aura Journal blog posts (brand voice)
# or skip image downloads:
python manage.py import_aura_images --no-images
```

### 6. Run
```bash
python manage.py runserver
```
- Storefront → http://localhost:8000
- Admin → http://localhost:8000/aura-admin/

---

## 🐳 Docker

```bash
docker-compose up --build
```
Spins up PostgreSQL, Redis, and the web app (gunicorn). Then:
```bash
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py seed_data
```

---

## 🎨 Tailwind (compiled, production-ready)

Styles are compiled to a single minified stylesheet at `static/css/tailwind.css`
(loaded via `{% static %}` in `base.html`) — no runtime CDN. The custom design
system (tokens, button classes, animations, dark mode) lives in `static/css/input.css`.

After changing any template classes or `input.css`, rebuild:
```bash
npm install        # first time only
npm run build:css  # one-off minified build
npm run watch:css  # or: rebuild on change during development
```
Then for deployment: `python manage.py collectstatic`.

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` / `False` |
| `DATABASE_URL` | `postgres://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Payment credentials |
| `UNSPLASH_ACCESS_KEY` / `PEXELS_API_KEY` | Image import |
| `USE_S3` + AWS keys | Enable S3 media in production |
| `EMAIL_*` | SMTP settings for order emails |
| `CSRF_TRUSTED_ORIGINS` | Production https origins (e.g. `https://yourdomain.com`) |
| `SENTRY_DSN` | Optional error tracking |

---

## 🚀 Production Deployment Checklist

```bash
# 1. Strong secret + production env
python -c "import secrets; print(secrets.token_urlsafe(64))"   # -> SECRET_KEY
#    set DEBUG=False, ALLOWED_HOSTS=yourdomain.com, CSRF_TRUSTED_ORIGINS=https://yourdomain.com
#    set a Postgres DATABASE_URL, real RAZORPAY_* keys, EMAIL_* SMTP, USE_S3=True (+AWS keys)

export DJANGO_SETTINGS_MODULE=aura_archives.settings.production

# 2. Build assets + DB
npm install && npm run build:css
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_data        # site settings, pages, coupons, shipping

# 3. Verify & serve
python manage.py check --deploy   # security audit (HSTS, SSL, secure cookies — all enabled)
gunicorn aura_archives.wsgi:application --bind 0.0.0.0:8000 --workers 3
```
Production settings enable HSTS, SSL redirect, secure/HTTP-only cookies, nosniff, and `DENY` framing.
Or just run `docker-compose up --build` (Postgres + Redis + gunicorn).

---

## 🧪 Tests

```bash
pytest
# or
python manage.py test tests
```

---

## 🎨 Brand Palette

| Color | Hex |
|-------|-----|
| Ivory | `#F8F4EF` |
| Blush Pink | `#E8CFCF` |
| Soft Lavender | `#D8D0E8` |
| Champagne Gold | `#C9A86A` |
| Charcoal | `#333333` |

---

Made with 🤍 — *Light That Preserves Moments*
