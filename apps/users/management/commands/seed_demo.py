from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.events.models import Event, EventParticipant, EventStatus
from apps.users.models import Role, User

DEMO_PASSWORD = "demo12345"
ORGANIZER_PHONE = "+12000000000"
MEMBER_PHONES = [f"+1200000000{i}" for i in range(1, 5)]
DEMO_TITLE = "Demo Secret Santa"


class Command(BaseCommand):
    help = "Create demo users and a draw-ready event (idempotent)."

    def handle(self, *args, **options):
        call_command("seed_superadmin")

        organizer, _ = User.objects.get_or_create(
            phone=ORGANIZER_PHONE,
            defaults={"role": Role.ORGANIZER, "is_active": True},
        )
        organizer.set_password(DEMO_PASSWORD)
        organizer.role = Role.ORGANIZER
        organizer.is_active = True
        organizer.save()

        members = []
        for phone in MEMBER_PHONES:
            member, _ = User.objects.get_or_create(
                phone=phone, defaults={"role": Role.USER, "is_active": True}
            )
            member.set_password(DEMO_PASSWORD)
            member.is_active = True
            member.save()
            members.append(member)

        event = Event.objects.filter(organizer=organizer, title=DEMO_TITLE).first()
        if event is None:
            now = timezone.now()
            event = Event.objects.create(
                organizer=organizer,
                title=DEMO_TITLE,
                description="Demo event",
                status=EventStatus.CREATED,
                min_price=10,
                max_price=50,
                start_date=now + timedelta(days=7),
                end_date=now + timedelta(days=14),
                reg_deadline=now + timedelta(days=3),
            )
            for member in members:
                EventParticipant.objects.get_or_create(event=event, user=member)

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo ready. Organizer {ORGANIZER_PHONE} / {DEMO_PASSWORD}, "
                f"event '{DEMO_TITLE}' id={event.id} with "
                f"{event.participants.count()} participants (status {event.status})."
            )
        )
