from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates the initial superuser for SOC Council'

    def handle(self, *args, **options):
        User = get_user_model()
        # Django default username validator does not allow spaces.
        # Replacing space with underscore to ensure valid login.
        username = "SOC_Council"
        password = os.environ.get("ADMIN_PASSWORD", "7716362752")
        email = "soc_council@example.com"

        if not User.objects.filter(username=username).exists():
            self.stdout.write(f"Creating superuser '{username}'...")
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully."))
        else:
            self.stdout.write(f"Superuser '{username}' already exists.")
