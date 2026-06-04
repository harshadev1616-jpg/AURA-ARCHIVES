from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Product


@receiver(pre_save, sender=Product)
def capture_old_stock(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_stock = Product.objects.get(pk=instance.pk).stock
        except Product.DoesNotExist:
            instance._old_stock = None
    else:
        instance._old_stock = None


@receiver(post_save, sender=Product)
def notify_back_in_stock(sender, instance, created, **kwargs):
    """When a product goes from out-of-stock to in-stock, email everyone waiting."""
    if created:
        return
    old = getattr(instance, "_old_stock", None)
    if old is None:
        return
    if old <= 0 and instance.stock > 0:
        pending = instance.stock_notifications.filter(is_notified=False)
        if not pending.exists():
            return
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        for note in pending:
            try:
                html = render_to_string("emails/back_in_stock.html", {
                    "product": instance, "site_url": settings.SITE_URL,
                })
                send_mail(
                    f"{instance.name} is back in stock — Aura Archives",
                    "", settings.DEFAULT_FROM_EMAIL, [note.email], html_message=html,
                )
            except Exception as e:
                print(f"Back-in-stock email error: {e}")
            note.is_notified = True
            note.notified_at = timezone.now()
            note.save(update_fields=["is_notified", "notified_at"])
