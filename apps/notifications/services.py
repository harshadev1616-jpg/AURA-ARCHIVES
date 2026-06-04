from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def notify_return_update(return_request, decision, amount=None):
    """Notify the customer about a return/refund decision (email + in-app)."""
    try:
        from .models import Notification
        order = return_request.order
        user = return_request.user
        if decision == "approved":
            subject = f"Refund approved for order #{order.order_number}"
            msg = (f"Good news — your return for order #{order.order_number} has been approved. "
                   f"A refund of Rs.{amount} is on its way and should reflect in 5–7 business days.")
        else:
            subject = f"Update on your return for order #{order.order_number}"
            msg = (f"We've reviewed your return request for order #{order.order_number}. "
                   f"Unfortunately we couldn't approve it this time. Reply to this email and we'll help.")
        if user and user.email:
            send_mail(subject, msg, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
            Notification.objects.create(
                user=user, notification_type=f"return_{decision}",
                title=subject, message=msg, link=f"/orders/{order.pk}/",
            )
    except Exception as e:
        print(f"Return notification error: {e}")


def notify_admins_new_order(order):
    """Alert staff of a new order: email + in-app notification listing the products."""
    try:
        from django.contrib.auth import get_user_model
        from .models import Notification
        from apps.core.models import SiteSettings

        items = list(order.items.all())
        lines = [f"{i.product_name} (ID {i.product_id}) ×{i.quantity} — Rs.{i.line_total}" for i in items]
        items_text = "\n".join(lines) if lines else "No items"
        first = items[0].product_name if items else "items"
        extra = (f" + {len(items) - 1} more" if len(items) > 1 else "")
        short = f"{first}{extra}"

        subject = f"New order #{order.order_number} — {short}"
        body = (
            f"New order received!\n\n"
            f"Order: #{order.order_number}\n"
            f"Customer: {order.shipping_full_name}"
            f"{' (' + order.user.email + ')' if order.user else ''}\n"
            f"Total: Rs.{order.total}  ·  Payment: {order.get_payment_method_display()}\n\n"
            f"Products:\n{items_text}\n\n"
            f"Manage: {settings.SITE_URL}/aura-admin/orders/order/{order.pk}/change/"
        )

        # Email the store inbox (and superusers as fallback)
        User = get_user_model()
        site = SiteSettings.get_settings()
        recipients = []
        if site.contact_email:
            recipients.append(site.contact_email)
        recipients += list(
            User.objects.filter(is_superuser=True, is_active=True)
            .exclude(email="").values_list("email", flat=True)
        )
        recipients = list({r for r in recipients if r})
        if recipients:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)

        # In-app notification for every staff member (shows in their notifications)
        staff = User.objects.filter(is_staff=True, is_active=True)
        for member in staff:
            Notification.objects.create(
                user=member,
                notification_type="admin_new_order",
                title=f"New order #{order.order_number}",
                message=f"{short} · Rs.{order.total} · {order.shipping_full_name}",
                link=f"/aura-admin/orders/order/{order.pk}/change/",
            )
    except Exception as e:
        print(f"Admin order notification error: {e}")


def send_order_notification(order, event_type):
    try:
        subject_map = {
            "order_placed": f"Order Confirmed #{order.order_number} - Aura Archives",
            "order_shipped": f"Your order #{order.order_number} has been shipped!",
            "order_delivered": f"Order #{order.order_number} delivered!",
            "order_cancelled": f"Order #{order.order_number} cancelled",
        }
        subject = subject_map.get(event_type, "Aura Archives Order Update")
        ctx = {"order": order, "site_name": "Aura Archives", "site_url": settings.SITE_URL}
        html_message = render_to_string(f"emails/{event_type}.html", ctx)
        if order.user:
            send_mail(
                subject, "", settings.DEFAULT_FROM_EMAIL,
                [order.user.email], html_message=html_message
            )
        from .models import EmailLog
        EmailLog.objects.create(
            to_email=order.user.email if order.user else "",
            subject=subject, template=event_type,
            context_data={"order_id": order.pk},
            status="sent",
        )
        from .models import Notification
        if order.user:
            Notification.objects.create(
                user=order.user,
                notification_type=event_type,
                title=subject,
                message=f"Your order #{order.order_number} status update",
                link=f"/orders/{order.pk}/",
            )
    except Exception as e:
        print(f"Notification error: {e}")
