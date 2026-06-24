from datetime import timedelta

import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from apps.chat.models import ChatMessage
from apps.events.models import Assignment, Event, EventStatus
from apps.users.models import User
from config.asgi import application


def _make_pair(status=EventStatus.ACTIVE, suffix="0"):
    now = timezone.now()
    santa = User.objects.create_user(phone=f"+1300100{suffix}1", password="x", is_active=True)
    ward = User.objects.create_user(phone=f"+1300100{suffix}2", password="x", is_active=True)
    event = Event.objects.create(
        organizer=santa,
        title="Chat event",
        status=status,
        start_date=now + timedelta(days=1),
        end_date=now + timedelta(days=2),
        reg_deadline=now,
    )
    assignment = Assignment.objects.create(event=event, santa=santa, ward=ward)
    return santa, ward, assignment


def _connect(user, assignment):
    token = str(AccessToken.for_user(user))
    return WebsocketCommunicator(application, f"/ws/chat/{assignment.id}?token={token}")


@pytest.mark.django_db(transaction=True)
async def test_member_can_connect_send_and_anonymity():
    santa, ward, assignment = await sync_to_async(_make_pair)(suffix="1")
    comm = _connect(santa, assignment)
    connected, _ = await comm.connect()
    assert connected is True

    await comm.send_json_to({"body": "Привет!"})
    resp = await comm.receive_json_from()
    assert resp == {"from": "Санта", "body": "Привет!"}
    assert santa.phone not in str(resp)
    assert str(santa.id) not in str(resp)
    await comm.disconnect()

    count = await sync_to_async(
        ChatMessage.objects.filter(assignment=assignment, sender=santa).count
    )()
    assert count == 1


@pytest.mark.django_db(transaction=True)
async def test_ward_sees_santa_label():
    santa, ward, assignment = await sync_to_async(_make_pair)(suffix="2")
    comm = _connect(ward, assignment)
    connected, _ = await comm.connect()
    assert connected is True
    await comm.send_json_to({"body": "hi"})
    resp = await comm.receive_json_from()
    assert resp["from"] == "Подопечный"
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_outsider_is_rejected():
    santa, ward, assignment = await sync_to_async(_make_pair)(suffix="3")
    outsider = await sync_to_async(User.objects.create_user)(
        phone="+13001009", password="x", is_active=True
    )
    comm = _connect(outsider, assignment)
    connected, _ = await comm.connect()
    assert connected is False


@pytest.mark.django_db(transaction=True)
async def test_chat_closed_when_event_not_active():
    santa, ward, assignment = await sync_to_async(_make_pair)(
        status=EventStatus.CREATED, suffix="4"
    )
    comm = _connect(santa, assignment)
    connected, _ = await comm.connect()
    assert connected is False


@pytest.mark.django_db(transaction=True)
async def test_unauthenticated_rejected():
    santa, ward, assignment = await sync_to_async(_make_pair)(suffix="5")
    comm = WebsocketCommunicator(application, f"/ws/chat/{assignment.id}")
    connected, _ = await comm.connect()
    assert connected is False
