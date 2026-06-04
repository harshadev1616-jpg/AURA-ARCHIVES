from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import F
import json
from .models import Review
from apps.products.models import Product
from apps.orders.models import OrderItem


@login_required
@require_POST
def submit_review(request):
    """Accepts JSON or multipart (with optional photo)."""
    if request.content_type and request.content_type.startswith("multipart"):
        product_id = request.POST.get("product_id")
        rating = request.POST.get("rating")
        title = request.POST.get("title", "")
        body = request.POST.get("body", "")
        image = request.FILES.get("image")
    else:
        data = json.loads(request.body)
        product_id = data.get("product_id")
        rating = data.get("rating")
        title = data.get("title", "")
        body = data.get("body", "")
        image = None

    if not body:
        return JsonResponse({"success": False, "message": "Please write your review"})
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"success": False, "message": "Product not found"})

    is_verified = OrderItem.objects.filter(
        order__user=request.user, product=product, order__payment_status="paid"
    ).exists()
    defaults = {
        "rating": rating, "title": title, "body": body,
        "is_verified_purchase": is_verified, "is_approved": False,
    }
    if image:
        defaults["image"] = image
    Review.objects.update_or_create(product=product, user=request.user, defaults=defaults)
    return JsonResponse({"success": True, "message": "Thank you! Your review is in for approval."})


@require_POST
def mark_helpful(request):
    """Increment a review's helpful count, deduped per session."""
    data = json.loads(request.body)
    review_id = data.get("review_id")
    voted = request.session.get("helpful_votes", [])
    if review_id in voted:
        return JsonResponse({"success": False, "message": "You've already marked this helpful"})
    try:
        Review.objects.filter(pk=review_id).update(helpful_count=F("helpful_count") + 1)
        review = Review.objects.get(pk=review_id)
    except Review.DoesNotExist:
        return JsonResponse({"success": False, "message": "Review not found"}, status=404)
    voted.append(review_id)
    request.session["helpful_votes"] = voted
    return JsonResponse({"success": True, "helpful_count": review.helpful_count})
