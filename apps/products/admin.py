from decimal import Decimal
from django import forms
from django.contrib import admin
from django.db.models import F
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from .models import Category, Product, ProductImage, ProductVariant, Tag, StockNotification


class MultipleFileInput(forms.ClearableFileInput):
    """A file input that accepts several files at once."""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"multiple": True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data if d]
        if data:
            return [single(data, initial)]
        return []


class ProductAdminForm(forms.ModelForm):
    """Adds a bulk multi-image upload field to the product change form."""
    bulk_images = MultipleFileField(
        required=False,
        label="Upload images",
        help_text="Select several photos at once — each becomes an image for this "
                  "product. Manage order / primary / alt text in “Product images” below.",
    )

    class Meta:
        model = Product
        fields = "__all__"


@admin.register(StockNotification)
class StockNotificationAdmin(admin.ModelAdmin):
    list_display = ["email", "product", "is_notified", "created_at", "notified_at"]
    list_filter = ["is_notified", "created_at"]
    search_fields = ["email", "product__name"]
    readonly_fields = ["created_at", "notified_at"]
    list_select_related = ["product"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "product_count", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]
    list_filter = ["is_active", "parent"]
    fieldsets = (
        ("Basic Info", {"fields": ("name", "slug", "parent", "image", "icon")}),
        ("Storytelling", {"fields": ("tagline", "story", "description"), "description": "The narrative that introduces this collection."}),
        ("Status", {"fields": ("is_active", "sort_order")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "is_primary", "alt_text", "sort_order"]


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ["name", "value", "price_adjustment", "stock", "sku", "is_active"]


class OnOfferFilter(admin.SimpleListFilter):
    """Filter the changelist by whether a product is currently on offer."""
    title = "offer status"
    parameter_name = "on_offer"

    def lookups(self, request, model_admin):
        return [("yes", "On offer"), ("no", "Not on offer")]

    def queryset(self, request, qs):
        on_offer = qs.filter(compare_price__isnull=False, compare_price__gt=F("price"))
        if self.value() == "yes":
            return on_offer
        if self.value() == "no":
            return qs.exclude(pk__in=on_offer.values("pk"))
        return qs


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    list_display = ["product_image_preview", "name", "category", "price_display", "offer_badge", "stock_badge", "is_active", "is_featured", "is_bestseller"]
    list_display_links = ["name"]
    list_editable = ["is_active", "is_featured", "is_bestseller"]
    list_filter = [OnOfferFilter, "is_active", "is_featured", "is_bestseller", "is_new", "category"]
    search_fields = ["name", "sku", "description"]
    prepopulated_fields = {"slug": ["name"]}
    form = ProductAdminForm
    inlines = [ProductImageInline, ProductVariantInline]
    readonly_fields = ["sku", "created_at", "updated_at", "average_rating", "review_count", "live_discount"]
    save_on_top = True
    fieldsets = (
        ("Basic Info", {"fields": ("name", "slug", "category", "tags", "sku")}),
        ("Images", {
            "fields": ("bulk_images",),
            "description": "Upload several photos at once for this product. The first one becomes the primary image if none is set.",
        }),
        ("Description", {"fields": ("short_description", "description", "ingredients", "care_instructions")}),
        ("Storytelling", {"fields": ("moment", "story", "ritual"), "description": "The narrative that makes each candle feel personal."}),
        ("Candle Details", {"fields": ("fragrance_notes", "notes_top", "notes_heart", "notes_base", "fragrance_strength", "burn_time_min", "burn_time_max", "wax_type", "wick_type", "weight", "dimensions")}),
        ("Pricing & Offer", {
            "fields": ("price", "compare_price", "live_discount", "cost_price"),
            "description": "To put a product ON OFFER: set <b>compare_price</b> to the original (higher) price and lower <b>price</b>. The discount badge shows automatically. Or select products in the list and use the <b>'Put on offer'</b> actions.",
        }),
        ("Inventory", {"fields": ("stock", "low_stock_threshold", "track_inventory")}),
        ("Status", {"fields": ("is_active", "is_featured", "is_bestseller", "is_new", "is_gift_ready", "sort_order")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
        ("Stats", {"fields": ("average_rating", "review_count", "created_at", "updated_at"), "classes": ("collapse",)}),
    )
    filter_horizontal = ["tags"]
    actions = [
        "offer_10", "offer_20", "offer_30", "remove_offer",
        "mark_featured", "mark_bestseller", "mark_new",
        "activate", "deactivate",
    ]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        files = form.cleaned_data.get("bulk_images") or []
        if not files:
            return
        product = form.instance
        start = product.images.count()
        has_primary = product.images.filter(is_primary=True).exists()
        for i, f in enumerate(files):
            ProductImage.objects.create(
                product=product,
                image=f,
                is_primary=(not has_primary and i == 0),
                sort_order=start + i,
            )
        self.message_user(request, f"Uploaded {len(files)} image(s) for {product.name}.")

    # ---- display helpers ----
    def product_image_preview(self, obj):
        img = obj.primary_image
        if img:
            return format_html("<img src={} height=44 style='border-radius:6px;object-fit:cover' />", img.image.url)
        return "—"
    product_image_preview.short_description = ""

    def price_display(self, obj):
        if obj.compare_price and obj.compare_price > obj.price:
            return format_html("<b>₹{}</b> <s style='color:#999'>₹{}</s>", obj.price, obj.compare_price)
        return format_html("₹{}", obj.price)
    price_display.short_description = "Price"

    def offer_badge(self, obj):
        if obj.discount_percentage > 0:
            return format_html("<span style='background:#B8945A;color:#fff;padding:2px 8px;border-radius:10px;font-size:11px'>−{}%</span>", obj.discount_percentage)
        return format_html("<span style='color:#bbb'>—</span>")
    offer_badge.short_description = "Offer"

    def stock_badge(self, obj):
        if not obj.track_inventory:
            return format_html("<span style='color:#888'>∞</span>")
        color = "#16a34a" if obj.stock > obj.low_stock_threshold else ("#dc2626" if obj.stock == 0 else "#d97706")
        return format_html("<b style='color:{}'>{}</b>", color, obj.stock)
    stock_badge.short_description = "Stock"

    def live_discount(self, obj):
        return f"{obj.discount_percentage}% off" if obj.discount_percentage else "Not on offer"
    live_discount.short_description = "Current discount"

    # ---- bulk actions ----
    def _apply_offer(self, request, queryset, pct):
        n = 0
        for p in queryset:
            base = p.compare_price if (p.compare_price and p.compare_price > p.price) else p.price
            p.compare_price = base
            p.price = (base * (Decimal(100 - pct) / Decimal(100))).quantize(Decimal("0.01"))
            p.save(update_fields=["price", "compare_price"])
            n += 1
        self.message_user(request, f"{n} product(s) put on offer at {pct}% off.")

    @admin.action(description="🏷  Put on offer — 10%% off")
    def offer_10(self, request, queryset):
        self._apply_offer(request, queryset, 10)

    @admin.action(description="🏷  Put on offer — 20%% off")
    def offer_20(self, request, queryset):
        self._apply_offer(request, queryset, 20)

    @admin.action(description="🏷  Put on offer — 30%% off")
    def offer_30(self, request, queryset):
        self._apply_offer(request, queryset, 30)

    @admin.action(description="Remove offer (restore original price)")
    def remove_offer(self, request, queryset):
        n = 0
        for p in queryset:
            if p.compare_price and p.compare_price > p.price:
                p.price = p.compare_price
                p.compare_price = None
                p.save(update_fields=["price", "compare_price"])
                n += 1
        self.message_user(request, f"Offer removed from {n} product(s).")

    @admin.action(description="Mark as Featured")
    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} product(s) marked featured.")

    @admin.action(description="Mark as Bestseller")
    def mark_bestseller(self, request, queryset):
        queryset.update(is_bestseller=True)
        self.message_user(request, f"{queryset.count()} product(s) marked bestseller.")

    @admin.action(description="Mark as New")
    def mark_new(self, request, queryset):
        queryset.update(is_new=True)

    @admin.action(description="Activate (show in store)")
    def activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate (hide from store)")
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
