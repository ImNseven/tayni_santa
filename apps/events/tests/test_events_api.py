from datetime import timedelta

import pytest
from django.utils import timezone

from apps.events.models import Assignment, Event
from apps.users.models import Role


def _payload(reg_deadline=None):
    now = timezone.now()
    return {
        "title": "Office Santa",
        "description": "Yearly",
        "min_price": 10,
        "max_price": 50,
        "start_date": (now + timedelta(days=2)).isoformat(),
        "end_date": (now + timedelta(days=3)).isoformat(),
        "reg_deadline": (reg_deadline or now + timedelta(days=1)).isoformat(),
    }


@pytest.mark.django_db
def test_user_cannot_create_event(auth, make_user):
    client = auth(make_user(phone="+12025571001", role=Role.USER))
    assert client.post("/api/events", _payload(), format="json").status_code == 403


@pytest.mark.django_db
def test_organizer_creates_event(auth, make_user):
    client = auth(make_user(phone="+12025571002", role=Role.ORGANIZER))
    resp = client.post("/api/events", _payload(), format="json")
    assert resp.status_code == 201
    assert resp.json()["status"] == "CREATED"


@pytest.mark.django_db
def test_price_validation(auth, make_user):
    client = auth(make_user(phone="+12025571003", role=Role.ORGANIZER))
    bad = _payload()
    bad["min_price"], bad["max_price"] = 100, 10
    assert client.post("/api/events", bad, format="json").status_code == 400


@pytest.mark.django_db
def test_join_after_deadline_rejected(auth, make_user):
    organizer = make_user(phone="+12025571004", role=Role.ORGANIZER)
    now = timezone.now()
    event = Event.objects.create(
        organizer=organizer,
        title="Past",
        start_date=now + timedelta(days=2),
        end_date=now + timedelta(days=3),
        reg_deadline=now - timedelta(minutes=1),
    )
    client = auth(make_user(phone="+12025571005"))
    assert client.post(f"/api/events/{event.id}/join", {}, format="json").status_code == 400


@pytest.mark.django_db
def test_full_draw_flow(auth, make_user):
    organizer = make_user(phone="+12025571100", role=Role.ORGANIZER)
    client = auth(organizer)
    event_id = client.post("/api/events", _payload(), format="json").json()["id"]

    members = [make_user(phone=f"+1202557120{i}") for i in range(4)]
    for m in members:
        resp = client.post(
            f"/api/events/{event_id}/participants", {"user_id": str(m.id)}, format="json"
        )
        assert resp.status_code == 201

    draw = client.post(f"/api/events/{event_id}/draw", format="json")
    assert draw.status_code == 200
    assert draw.json()["status"] == "ACTIVE"

    assignments = Assignment.objects.filter(event_id=event_id)
    santas = [a.santa_id for a in assignments]
    wards = [a.ward_id for a in assignments]
    member_ids = {m.id for m in members}

    assert len(assignments) == 4
    assert set(santas) == member_ids
    assert set(wards) == member_ids
    assert all(a.santa_id != a.ward_id for a in assignments)


@pytest.mark.django_db
def test_draw_needs_two_participants(auth, make_user):
    organizer = make_user(phone="+12025571300", role=Role.ORGANIZER)
    client = auth(organizer)
    event_id = client.post("/api/events", _payload(), format="json").json()["id"]
    client.post(
        f"/api/events/{event_id}/participants",
        {"user_id": str(make_user(phone="+12025571301").id)},
        format="json",
    )
    assert client.post(f"/api/events/{event_id}/draw", format="json").status_code == 400


@pytest.mark.django_db
def test_my_assignment_after_draw(auth, make_user):
    organizer = make_user(phone="+12025571400", role=Role.ORGANIZER)
    admin_client = auth(organizer)
    event_id = admin_client.post("/api/events", _payload(), format="json").json()["id"]
    members = [make_user(phone=f"+1202557141{i}") for i in range(3)]
    for m in members:
        admin_client.post(
            f"/api/events/{event_id}/participants", {"user_id": str(m.id)}, format="json"
        )
    admin_client.post(f"/api/events/{event_id}/draw", format="json")

    member_client = auth(members[0])
    resp = member_client.get(f"/api/events/{event_id}/my-assignment")
    assert resp.status_code == 200
    assert resp.json()["ward_phone"] in {m.phone for m in members}


@pytest.mark.django_db
def test_gift_sent_toggle_only_when_active(auth, make_user):
    organizer = make_user(phone="+12025571500", role=Role.ORGANIZER)
    client = auth(organizer)
    event_id = client.post("/api/events", _payload(), format="json").json()["id"]
    member = make_user(phone="+12025571501")
    client.post(f"/api/events/{event_id}/participants", {"user_id": str(member.id)}, format="json")

    member_client = auth(member)
    assert (
        member_client.post(
            f"/api/events/{event_id}/gift-sent", {"gift_sent": True}, format="json"
        ).status_code
        == 400
    )

    client.post(
        f"/api/events/{event_id}/participants",
        {"user_id": str(make_user(phone="+12025571502").id)},
        format="json",
    )
    client.post(f"/api/events/{event_id}/draw", format="json")
    ok = member_client.post(f"/api/events/{event_id}/gift-sent", {"gift_sent": True}, format="json")
    assert ok.status_code == 200 and ok.json()["gift_sent"] is True


@pytest.mark.django_db
def test_illegal_lifecycle_transition_returns_400(auth, make_user):
    organizer = make_user(phone="+12025571600", role=Role.ORGANIZER)
    client = auth(organizer)
    event_id = client.post("/api/events", _payload(), format="json").json()["id"]
    assert client.post(f"/api/events/{event_id}/complete", format="json").status_code == 400


@pytest.mark.django_db
def test_non_organizer_cannot_draw(auth, make_user):
    organizer = make_user(phone="+12025571700", role=Role.ORGANIZER)
    admin_client = auth(organizer)
    event_id = admin_client.post("/api/events", _payload(), format="json").json()["id"]
    for i in range(2):
        admin_client.post(
            f"/api/events/{event_id}/participants",
            {"user_id": str(make_user(phone=f"+1202557171{i}").id)},
            format="json",
        )
    other = auth(make_user(phone="+12025571720", role=Role.ORGANIZER))
    assert other.post(f"/api/events/{event_id}/draw", format="json").status_code == 403
