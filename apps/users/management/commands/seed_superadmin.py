import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the default superadmin if it does not exist (idempotent)."

    def handle(self, *args, **options):
        phone = os.environ.get("SUPERADMIN_PHONE", "+10000000000")
        password = os.environ.get("SUPERADMIN_PASSWORD", "admin12345")

        User = get_user_model()
        if User.objects.filter(phone=phone).exists():
            self.stdout.write(self.style.WARNING(f"Superadmin {phone} already exists."))
            return

        User.objects.create_superuser(phone=phone, password=password)
        self.stdout.write(self.style.SUCCESS(f"Superadmin {phone} created."))
