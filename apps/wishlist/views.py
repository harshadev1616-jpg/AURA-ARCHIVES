from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Wishlist
from apps.products.models import Product


@login_required
@require_POST
def toggle_wishlist(request):
    data = json.loads(request.body)
    product_id = data.get("product_id")
    try:
        product = Product.objects.get(pk=product_id)
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        if product in wishlist.products.all():
            wishlist.products.remove(product)
            in_wishlist = False
            msg = "Removed from wishlist"
        else:
            wishlist.products.add(product)
            in_wishlist = True
            msg = "Added to wishlist"
        return JsonResponse({"success": True, "in_wishlist": in_wishlist, "message": msg})
    except Product.DoesNotExist:
        return JsonResponse({"success": False, "message": "Product not found"})


@login_required
def wishlist_view(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    return render(request, "accounts/wishlist.html", {"wishlist": wishlist})
