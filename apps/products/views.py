from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from .models import Product, Category, Tag
from apps.reviews.models import Review
from apps.orders.cart import Cart
import json


class ProductListView(ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).prefetch_related('images').select_related('category')
        q = self.request.GET.get('q', '')
        category_slug = self.request.GET.get('category', '')
        sort = self.request.GET.get('sort', '-created_at')
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        tag = self.request.GET.get('tag', '')

        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(fragrance_notes__icontains=q))
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if price_min:
            qs = qs.filter(price__gte=price_min)
        if price_max:
            qs = qs.filter(price__lte=price_max)
        if tag:
            qs = qs.filter(tags__slug=tag)

        sort_map = {
            'price_asc': 'price', 'price_desc': '-price',
            'name': 'name', '-name': '-name',
            'newest': '-created_at', 'bestseller': '-is_bestseller',
        }
        qs = qs.order_by(sort_map.get(sort, '-created_at'))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.filter(is_active=True, parent=None)
        ctx['tags'] = Tag.objects.all()
        ctx['current_category'] = self.request.GET.get('category', '')
        ctx['current_sort'] = self.request.GET.get('sort', '')
        ctx['search_query'] = self.request.GET.get('q', '')
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).prefetch_related('images', 'variants', 'tags')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.object
        ctx['reviews'] = product.reviews.filter(is_approved=True).select_related('user')[:10]
        ctx['related_products'] = Product.objects.filter(
            category=product.category, is_active=True
        ).exclude(pk=product.pk)[:4]
        # "Complete the Ritual" — cross-sell from OTHER collections (loved candles first)
        ctx['pair_with'] = Product.objects.filter(is_active=True).exclude(
            pk=product.pk
        ).exclude(category=product.category).order_by(
            '-is_bestseller', '-is_featured', '?'
        )[:3]
        # Track recently viewed
        viewed = self.request.session.get('recently_viewed', [])
        if product.pk not in viewed:
            viewed.insert(0, product.pk)
        self.request.session['recently_viewed'] = viewed[:8]
        ctx['recently_viewed'] = Product.objects.filter(
            pk__in=viewed, is_active=True
        ).exclude(pk=product.pk)[:4]
        # Track product view analytics
        try:
            from apps.analytics.models import ProductView
            ProductView.objects.create(
                product=product,
                user=self.request.user if self.request.user.is_authenticated else None,
                session_key=self.request.session.session_key or '',
            )
        except Exception:
            pass
        return ctx


class CategoryDetailView(ListView):
    template_name = 'products/category.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        return Product.objects.filter(category=self.category, is_active=True).prefetch_related('images')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category'] = self.category
        ctx['categories'] = Category.objects.filter(is_active=True, parent=None)
        return ctx


# ============================================================
#  "Find Your Moment" — interactive scent quiz
# ============================================================

SCENT_QUIZ = [
    {
        "key": "feeling",
        "question": "What do you want your space to feel like?",
        "subtitle": "Close your eyes. Where do you want to be?",
        "options": [
            {"value": "calm", "label": "Calm & restful", "emoji": "🌿",
             "keywords": ["lavender", "chamomile", "calm", "rest", "wellness", "cotton", "eucalyptus"],
             "category": "Wellness"},
            {"value": "cosy", "label": "Warm & cosy", "emoji": "🤎",
             "keywords": ["vanilla", "amber", "sandalwood", "warm", "cosy", "tonka"],
             "category": "Classic"},
            {"value": "alive", "label": "Fresh & alive", "emoji": "🌸",
             "keywords": ["floral", "jasmine", "sunflower", "fresh", "garden", "citrus", "daisy", "bergamot"],
             "category": "Floral"},
            {"value": "bold", "label": "Bold & mysterious", "emoji": "🌙",
             "keywords": ["midnight", "dark", "oud", "black rose", "night", "cedar"],
             "category": "Classic"},
        ],
    },
    {
        "key": "time",
        "question": "When will you light it most?",
        "subtitle": "Every candle has its hour.",
        "options": [
            {"value": "morning", "label": "Slow mornings", "emoji": "☀️",
             "keywords": ["sunflower", "citrus", "fresh", "bright", "bergamot", "green tea"]},
            {"value": "evening", "label": "Wind-down evenings", "emoji": "🌅",
             "keywords": ["warm", "vanilla", "amber", "sandalwood"]},
            {"value": "night", "label": "Late, quiet nights", "emoji": "🌌",
             "keywords": ["night", "dark", "midnight", "jasmine", "oud", "black rose"]},
            {"value": "anytime", "label": "Any quiet moment", "emoji": "🕯️",
             "keywords": ["calm", "lavender", "soft", "cotton", "chamomile"]},
        ],
    },
    {
        "key": "note",
        "question": "Which note speaks to you?",
        "subtitle": "Follow your nose.",
        "options": [
            {"value": "flowers", "label": "Flowers in bloom", "emoji": "💐",
             "keywords": ["rose", "peony", "jasmine", "daisy", "floral", "wildflower"]},
            {"value": "sweet", "label": "Sweet & creamy", "emoji": "🍯",
             "keywords": ["vanilla", "sugar", "tonka", "amber", "honey"]},
            {"value": "herbal", "label": "Clean & herbal", "emoji": "🍃",
             "keywords": ["lavender", "eucalyptus", "chamomile", "cotton", "green tea", "mint"]},
            {"value": "woody", "label": "Deep & woody", "emoji": "🪵",
             "keywords": ["cedar", "sandalwood", "oud", "amber", "dark", "moss"]},
        ],
    },
    {
        "key": "who",
        "question": "And who is it for?",
        "subtitle": "A candle is a quiet kind of gift.",
        "options": [
            {"value": "me", "label": "A treat for me", "emoji": "🤍", "keywords": []},
            {"value": "love", "label": "Someone I love", "emoji": "💕",
             "keywords": ["rose", "heart", "romantic", "peony"], "category": "Gift Candles"},
            {"value": "newhome", "label": "A gift or new home", "emoji": "🎁",
             "keywords": ["gift", "set", "keepsake"], "category": "Gift Sets"},
            {"value": "unsure", "label": "Not sure yet", "emoji": "✨", "keywords": []},
        ],
    },
]


def scent_quiz(request):
    # Only expose what the front-end needs (no server-side scoring keywords leaked)
    public_quiz = [
        {
            "key": q["key"],
            "question": q["question"],
            "subtitle": q["subtitle"],
            "options": [{"value": o["value"], "label": o["label"], "emoji": o["emoji"]} for o in q["options"]],
        }
        for q in SCENT_QUIZ
    ]
    return render(request, "products/quiz.html", {"quiz_json": json.dumps(public_quiz)})


def _product_haystack(p):
    parts = [
        p.name, p.fragrance_notes, p.notes_top, p.notes_heart, p.notes_base,
        p.moment, p.story, p.short_description,
        p.category.name if p.category else "",
    ]
    return " ".join(parts).lower()


def scent_quiz_result(request):
    """Score every active candle against the chosen moods and return the best match."""
    if request.method != "POST":
        return JsonResponse({"success": False}, status=400)
    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

    answers = data.get("answers", {})  # {"feeling": "calm", "time": "evening", ...}

    # Aggregate keywords + category signals from the selected options
    keywords, category_weights = [], {}
    for q in SCENT_QUIZ:
        chosen = answers.get(q["key"])
        for opt in q["options"]:
            if opt["value"] == chosen:
                keywords.extend(opt.get("keywords", []))
                cat = opt.get("category")
                if cat:
                    category_weights[cat] = category_weights.get(cat, 0) + 1

    products = list(
        Product.objects.filter(is_active=True).select_related("category").prefetch_related("images")
    )
    if not products:
        return JsonResponse({"success": False, "message": "No candles available"}, status=404)

    scored = []
    for p in products:
        hay = _product_haystack(p)
        score = sum(3 for kw in keywords if kw in hay)  # keyword hits
        if p.category and p.category.name in category_weights:
            score += 6 * category_weights[p.category.name]  # strong category signal
        if p.is_bestseller:
            score += 1  # gentle tiebreaker toward loved candles
        scored.append((score, p))

    scored.sort(key=lambda t: t[0], reverse=True)
    # If everything tied at 0 (e.g. neutral answers), fall back to bestsellers
    if scored[0][0] == 0:
        scored.sort(key=lambda t: (t[1].is_bestseller, t[1].is_featured), reverse=True)

    def serialize(p):
        img = p.primary_image
        return {
            "name": p.name,
            "slug": p.slug,
            "url": p.get_absolute_url(),
            "moment": p.moment,
            "price": str(p.price),
            "compare_price": str(p.compare_price) if p.compare_price else None,
            "category": p.category.name if p.category else "",
            "notes": p.fragrance_notes,
            "image": img.image.url if img else "",
        }

    best = scored[0][1]
    alternates = [serialize(p) for _, p in scored[1:4]]
    return JsonResponse({"success": True, "match": serialize(best), "alternates": alternates})


def quick_view(request, slug):
    """Return a compact product card partial for the quick-view modal."""
    product = get_object_or_404(
        Product.objects.prefetch_related("images"), slug=slug, is_active=True
    )
    return render(request, "products/_quickview.html", {"product": product})


def notify_back_in_stock(request):
    """Register a 'notify me when back in stock' request."""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=400)
    data = json.loads(request.body)
    email = (data.get('email') or '').strip()
    slug = data.get('product_slug')
    product_id = data.get('product_id')
    if not email or '@' not in email:
        return JsonResponse({'success': False, 'message': 'Please enter a valid email'})
    try:
        if slug:
            product = Product.objects.get(slug=slug, is_active=True)
        else:
            product = Product.objects.get(pk=product_id, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    if product.is_in_stock:
        return JsonResponse({'success': False, 'message': 'Good news — this candle is already in stock!'})
    from .models import StockNotification
    StockNotification.objects.get_or_create(
        product=product, email=email,
        defaults={'user': request.user if request.user.is_authenticated else None},
    )
    return JsonResponse({'success': True, 'message': "We'll email you the moment it's back ✨"})


def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        product_slug = data.get('product_slug')
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))
        try:
            if product_slug:
                product = Product.objects.get(slug=product_slug, is_active=True)
            else:
                product = Product.objects.get(pk=product_id, is_active=True)
            variant = None
            if variant_id:
                variant = product.variants.get(pk=variant_id)
            cart = Cart(request)
            # Validate against available stock (existing cart qty + requested)
            from apps.orders.inventory import check_availability, available_stock
            key = f"{product.id}_{variant.id if variant else 'none'}"
            already = cart.cart.get(key, {}).get('quantity', 0)
            ok, avail, msg = check_availability(product, variant, already + quantity)
            if not ok:
                if avail == 0:
                    return JsonResponse({'success': False, 'message': "Sorry, this candle is out of stock."})
                return JsonResponse({'success': False, 'message': f"Only {avail} available — you already have {already} in your bag."})
            cart.add(product, variant, quantity)
            # Persist for logged-in users so we can recover abandoned carts
            if request.user.is_authenticated:
                from apps.orders.models import CartItem
                ci, _ = CartItem.objects.get_or_create(
                    user=request.user, product=product, variant=variant,
                    defaults={'quantity': 0},
                )
                ci.quantity = ci.quantity + quantity
                ci.reminder_sent = False
                ci.save()
            return JsonResponse({'success': True, 'cart_count': len(cart), 'message': 'Added to cart!'})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    return JsonResponse({'success': False}, status=400)


def update_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        variant_id = data.get('variant_id', 'none')
        quantity = int(data.get('quantity', 1))
        cart = Cart(request)
        cart.update(product_id, variant_id, quantity)
        return JsonResponse({'success': True, 'cart_count': len(cart), 'total': str(cart.total_price)})
    return JsonResponse({'success': False}, status=400)


def remove_from_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        variant_id = data.get('variant_id', 'none')
        cart = Cart(request)
        cart.remove(product_id, variant_id)
        return JsonResponse({'success': True, 'cart_count': len(cart), 'total': str(cart.total_price)})
    return JsonResponse({'success': False}, status=400)
