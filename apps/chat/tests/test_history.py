from datetime import timedelta

import pytest
from django.utils import timezone

from apps.chat.models import ChatMessage
from apps.events.models import Assignment, Event, EventStatus


def _pair(make_user, suffix):
    now = timezone.now()
    santa = make_user(phone=f"+1400100{suffix}1")
    ward = make_user(phone=f"+1400100{suffix}2")
    event = Event.objects.create(
        organizer=santa,
        title="E",
        status=EventStatus.ACTIVE,
        start_date=now + timedelta(days=1),
        end_date=now + timedelta(days=2),
        reg_deadline=now,
    )
    assignment = Assignment.objects.create(event=event, santa=santa, ward=ward)
    ChatMessage.objects.create(assignment=assignment, sender=santa, body="from santa")
    ChatMessage.objects.create(assignment=assignment, sender=ward, body="from ward")
    return santa, ward, assignment


@pytest.mark.django_db
def test_member_reads_anonymized_history(auth, make_user):
    santa, ward, assignment = _pair(make_user, "1")
    resp = auth(santa).get(f"/api/chat/{assignment.id}/messages")
    assert resp.status_code == 200
    body = resp.json()
    assert [m["from"] for m in body] == ["Санта", "Подопечный"]
    assert santa.phone not in str(body)
    assert ward.phone not in str(body)


@pytest.mark.django_db
def test_outsider_forbidden(auth, make_user):
    santa, ward, assignment = _pair(make_user, "2")
    outsider = make_user(phone="+14001009")
    assert auth(outsider).get(f"/api/chat/{assignment.id}/messages").status_code == 403


@pytest.mark.django_db
def test_superadmin_can_read(auth, make_user, superadmin):
    santa, ward, assignment = _pair(make_user, "3")
    assert auth(superadmin).get(f"/api/chat/{assignment.id}/messages").status_code == 200
