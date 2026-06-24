import pytest
from django.core.management import call_command

from apps.events.models import Event
from apps.events.services import run_draw
from apps.users.models import User


@pytest.mark.django_db
def test_seed_demo_creates_draw_ready_event():
    call_command("seed_demo")

    event = Event.objects.get(title="Demo Secret Santa")
    assert event.participants.count() == 4
    assert event.status == "CREATED"

    run_draw(event)
    event.refresh_from_db()
    assert event.status == "ACTIVE"
    assert event.assignments.count() == 4


@pytest.mark.django_db
def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    call_command("seed_demo")
    assert User.objects.filter(phone="+12000000000").count() == 1
    assert Event.objects.filter(title="Demo Secret Santa").count() == 1
