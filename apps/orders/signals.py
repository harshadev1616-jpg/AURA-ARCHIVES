from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Order


@receiver(pre_save, sender=Order)
def capture_old_status(sender, instance, **kwargs):
    """Remember the previous status so post_save can detect transitions."""
    if instance.pk:
        try:
            instance._old_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


# Map a new status -> the email event to send
STATUS_EVENT = {
    "confirmed": "order_placed",
    "shipped": "order_shipped",
    "out_for_delivery": "order_shipped",
    "delivered": "order_delivered",
    "cancelled": "order_cancelled",
}


@receiver(post_save, sender=Order)
def notify_on_status_change(sender, instance, created, **kwargs):
    old = getattr(instance, "_old_status", None)
    new = instance.status
    # Only act on a genuine transition (and on first confirmation)
    if new == old:
        return

    # --- Inventory: commit stock when an order becomes real, release on cancel ---
    try:
        from .inventory import deduct_for_order, restore_for_order, COMMITTED_STATUSES, RELEASED_STATUSES
        if new in COMMITTED_STATUSES:
            deduct_for_order(instance)
        elif new in RELEASED_STATUSES:
            restore_for_order(instance)
    except Exception as e:
        print(f"Inventory update error: {e}")

    event = STATUS_EVENT.get(new)
    if not event:
        return
    # Stamp delivered time once + award loyalty points
    if new == "delivered":
        if not instance.delivered_at:
            Order.objects.filter(pk=instance.pk).update(delivered_at=timezone.now())
        try:
            from apps.accounts.services import award_points_for_order, reward_referral_if_due
            award_points_for_order(instance)
            reward_referral_if_due(instance)
        except Exception as e:
            print(f"Loyalty award error: {e}")
    # Avoid sending a duplicate "placed" email if it was already confirmed before
    if event == "order_placed" and old not in (None, "pending"):
        return
    from apps.notifications.services import send_order_notification
    send_order_notification(instance, event)

    # Alert staff when a new order is placed (confirmed for the first time)
    if event == "order_placed":
        from apps.notifications.services import notify_admins_new_order
        notify_admins_new_order(instance)
