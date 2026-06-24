from datetime import timedelta

import pytest
from django.utils import timezone

from apps.events.models import Event, EventStatus
from apps.events.services import transition


def _event(user, status=EventStatus.CREATED):
    now = timezone.now()
    return Event.objects.create(
        organizer=user,
        title="E",
        status=status,
        start_date=now + timedelta(days=2),
        end_date=now + timedelta(days=3),
        reg_deadline=now + timedelta(days=1),
    )


@pytest.mark.django_db
def test_allowed_transition(make_user):
    event = _event(make_user(phone="+12025570001"))
    transition(event, EventStatus.ACTIVE)
    assert event.status == EventStatus.ACTIVE


@pytest.mark.django_db
def test_illegal_transition_raises(make_user):
    event = _event(make_user(phone="+12025570002"), status=EventStatus.COMPLETED)
    with pytest.raises(ValueError):
        transition(event, EventStatus.ACTIVE)


@pytest.mark.django_db
def test_archived_is_terminal(make_user):
    event = _event(make_user(phone="+12025570003"), status=EventStatus.ARCHIVED)
    with pytest.raises(ValueError):
        transition(event, EventStatus.COMPLETED)
