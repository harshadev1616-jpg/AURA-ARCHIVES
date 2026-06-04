from django import template
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

register = template.Library()


def _sales_series(paid, today, days=14):
    """Daily revenue for the last `days` days as render-ready SVG bar data."""
    start = today - timedelta(days=days - 1)
    rows = (paid.filter(created_at__date__gte=start)
            .annotate(d=TruncDate("created_at")).values("d")
            .annotate(total=Sum("total")))
    by_day = {r["d"]: float(r["total"] or 0) for r in rows}
    series = []
    for i in range(days):
        day = start + timedelta(days=i)
        series.append({"label": day.strftime("%d %b"), "short": day.strftime("%d"), "amount": by_day.get(day, 0)})
    peak = max((s["amount"] for s in series), default=0) or 1
    # bar geometry for an inline 100-height SVG
    for s in series:
        s["h"] = round(max(2, (s["amount"] / peak) * 92), 1)
    return series, peak


@register.inclusion_tag("admin/_aura_dashboard.html", takes_context=True)
def aura_dashboard(context):
    from apps.orders.models import Order
    from apps.accounts.models import User
    from apps.products.models import Product, StockNotification
    from apps.reviews.models import Review
    from apps.notifications.models import Notification

    request = context.get("request")
    today = timezone.now().date()
    last_30 = today - timedelta(days=30)
    last_7 = today - timedelta(days=7)

    paid = Order.objects.filter(payment_status="paid")
    revenue = paid.aggregate(s=Sum("total"))["s"] or 0
    paid_count = paid.count()

    alerts = []
    alert_count = 0
    if request is not None:
        qs = Notification.objects.filter(user=request.user, notification_type="admin_new_order", is_read=False)
        alert_count = qs.count()
        alerts = list(qs.order_by("-created_at")[:6])

    sales_series, sales_peak = _sales_series(paid, today, days=14)
    sales_14 = sum(s["amount"] for s in sales_series)

    return {
        "sales_series": sales_series,
        "sales_peak": sales_peak,
        "sales_14": sales_14,
        "revenue": revenue,
        "revenue_30": paid.filter(created_at__date__gte=last_30).aggregate(s=Sum("total"))["s"] or 0,
        "orders_total": Order.objects.count(),
        "orders_7": Order.objects.filter(created_at__date__gte=last_7).count(),
        "aov": (revenue / paid_count) if paid_count else 0,
        "customers": User.objects.filter(is_staff=False).count(),
        "new_customers_30": User.objects.filter(is_staff=False, date_joined__date__gte=last_30).count(),
        "orders_to_fulfil": Order.objects.filter(status__in=["confirmed", "processing"]).count(),
        "pending_reviews": Review.objects.filter(is_approved=False).count(),
        "restock_requests": StockNotification.objects.filter(is_notified=False).count(),
        "low_stock": Product.objects.filter(is_active=True, stock__lte=5, stock__gt=0).order_by("stock")[:5],
        "low_stock_count": Product.objects.filter(is_active=True, stock__lte=5, stock__gt=0).count(),
        "alerts": alerts,
        "alert_count": alert_count,
    }
