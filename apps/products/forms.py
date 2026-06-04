from django import forms
from .models import Product, Category, ProductImage, ProductVariant


class ProductFilterForm(forms.Form):
    SORT_CHOICES = [
        ("newest", "Newest"),
        ("price_asc", "Price: Low to High"),
        ("price_desc", "Price: High to Low"),
        ("bestseller", "Bestsellers"),
        ("name", "Name A-Z"),
    ]
    q = forms.CharField(required=False)
    category = forms.CharField(required=False)
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False)
    price_min = forms.DecimalField(required=False, min_value=0)
    price_max = forms.DecimalField(required=False, min_value=0)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ["slug", "sku", "deleted_at"]
