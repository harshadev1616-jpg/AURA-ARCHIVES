from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Email logged-in users who left items in their cart (no order since)."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=4, help="Cart idle threshold in hours")
        parser.add_argument("--dry-run", action="store_true", help="List who would be emailed, send nothing")

    def handle(self, *args, **options):
        from apps.orders.models import CartItem, Order
        from apps.accounts.models import User

        cutoff = timezone.now() - timedelta(hours=options["hours"])
        # Users with un-reminded cart items idle past the cutoff
        user_ids = (
            CartItem.objects.filter(user__isnull=False, reminder_sent=False, updated_at__lte=cutoff)
            .values_list("user_id", flat=True).distinct()
        )

        sent = 0
        for uid in user_ids:
            try:
                user = User.objects.get(pk=uid)
            except User.DoesNotExist:
                continue
            items = list(CartItem.objects.filter(user=user, reminder_sent=False).select_related("product", "variant"))
            if not items:
                continue
            # Skip if they placed any order after the most recent cart activity
            latest_item = max(i.updated_at for i in items)
            if Order.objects.filter(user=user, created_at__gte=latest_item).exists():
                CartItem.objects.filter(user=user).update(reminder_sent=True)
                continue

            self.stdout.write(f"  → {user.email} ({len(items)} item(s))")
            if options["dry_run"]:
                continue
            try:
                html = render_to_string("emails/abandoned_cart.html", {
                    "user": user, "items": items, "site_url": settings.SITE_URL,
                })
                send_mail(
                    "You left a moment behind — Aura Archives",
                    "", settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html,
                )
                from apps.notifications.models import EmailLog
                EmailLog.objects.create(to_email=user.email, subject="Abandoned cart reminder",
                                        template="abandoned_cart", status="sent")
                sent += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    error: {e}"))
                continue
            CartItem.objects.filter(user=user).update(reminder_sent=True)

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("Dry run complete — no emails sent."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Sent {sent} abandoned-cart reminder(s)."))
