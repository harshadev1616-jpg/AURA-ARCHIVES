import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Create or update a superuser from the ADMIN_EMAIL / ADMIN_PASSWORD "
        "environment variables. Idempotent and safe to run on every deploy. "
        "Does nothing if ADMIN_PASSWORD is not set."
    )

    def handle(self, *args, **options):
        email = os.environ.get("ADMIN_EMAIL", "admin@aura-archives.com").strip()
        password = os.environ.get("ADMIN_PASSWORD", "").strip()

        if not password:
            self.stdout.write("ensure_admin: ADMIN_PASSWORD not set — skipping.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"is_staff": True, "is_superuser": True, "is_active": True},
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"ensure_admin: superuser {'created' if created else 'updated'} — {email}"
            )
        )
