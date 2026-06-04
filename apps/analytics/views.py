from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta


@staff_member_required
def analytics_dashboard(request):
    from apps.orders.models import Order, OrderItem
    from apps.accounts.models import User
    from apps.products.models import Product, StockNotification
    from apps.reviews.models import Review
    from apps.notifications.models import Notification
    from django.shortcuts import redirect

    # Dismiss new-order alerts for this admin
    if request.GET.get("clear_alerts"):
        Notification.objects.filter(user=request.user, notification_type="admin_new_order", is_read=False).update(is_read=True)
        return redirect("analytics:dashboard")

    today = timezone.now().date()
    last_30 = today - timedelta(days=30)
    last_7 = today - timedelta(days=7)

    paid = Order.objects.filter(payment_status="paid")
    total_revenue = paid.aggregate(Sum("total"))["total__sum"] or 0
    paid_count = paid.count()
    aov = (total_revenue / paid_count) if paid_count else 0

    # Top products by units sold
    top_products = (
        OrderItem.objects.values("product_name")
        .annotate(units=Sum("quantity"), revenue=Sum("price"))
        .order_by("-units")[:5]
    )

    # Most viewed products (from ProductView analytics)
    try:
        from apps.analytics.models import ProductView
        most_viewed = (
            ProductView.objects.values("product__name")
            .annotate(views=Count("id"))
            .order_by("-views")[:5]
        )
    except Exception:
        most_viewed = []

    # Bundle orders = orders whose notes mention the bundle saving
    bundle_orders = Order.objects.filter(notes__icontains="Bundle saving").count()

    # New-order alerts for THIS admin (unread "new order" notifications)
    from apps.notifications.models import Notification
    new_order_alerts = Notification.objects.filter(
        user=request.user, notification_type="admin_new_order", is_read=False
    ).order_by("-created_at")[:15]
    new_order_alert_count = Notification.objects.filter(
        user=request.user, notification_type="admin_new_order", is_read=False
    ).count()
    # Orders needing action = paid/confirmed but not yet shipped/delivered
    orders_to_process = Order.objects.filter(status__in=["confirmed", "processing"]).count()

    context = {
        "total_orders": Order.objects.count(),
        "total_revenue": total_revenue,
        "aov": aov,
        "orders_last_7": Order.objects.filter(created_at__date__gte=last_7).count(),
        "revenue_last_30": paid.filter(created_at__date__gte=last_30).aggregate(Sum("total"))["total__sum"] or 0,
        "total_customers": User.objects.filter(is_staff=False).count(),
        "new_customers_30": User.objects.filter(is_staff=False, date_joined__date__gte=last_30).count(),
        "total_products": Product.objects.filter(is_active=True).count(),
        "recent_orders": Order.objects.select_related("user").order_by("-created_at")[:10],
        "low_stock_products": Product.objects.filter(is_active=True, stock__lte=5, stock__gt=0).order_by("stock"),
        "out_of_stock": Product.objects.filter(is_active=True, stock=0, track_inventory=True),
        "top_products": top_products,
        "most_viewed": most_viewed,
        "bundle_orders": bundle_orders,
        "pending_reviews": Review.objects.filter(is_approved=False).count(),
        "pending_restock_requests": StockNotification.objects.filter(is_notified=False).count(),
        "orders_by_status": Order.objects.values("status").annotate(c=Count("id")).order_by("-c"),
        "new_order_alerts": new_order_alerts,
        "new_order_alert_count": new_order_alert_count,
        "orders_to_process": orders_to_process,
    }
    return render(request, "admin/analytics_dashboard.html", context)
