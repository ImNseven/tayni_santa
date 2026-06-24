from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.wishlists.models import Wishlist

from .draw import assign_santas
from .models import Assignment, Event, EventParticipant, EventStatus

ALLOWED = {
    EventStatus.CREATED: {EventStatus.ACTIVE},
    EventStatus.ACTIVE: {EventStatus.COMPLETED},
    EventStatus.COMPLETED: {EventStatus.ARCHIVED},
    EventStatus.ARCHIVED: set(),
}


def transition(event: Event, new_status: str) -> None:
    if new_status not in ALLOWED[event.status]:
        raise ValueError(f"Illegal transition {event.status} -> {new_status}")
    event.status = new_status
    event.save(update_fields=["status"])


def _transition_or_400(event: Event, new_status: str) -> None:
    try:
        transition(event, new_status)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def create_event(
    organizer,
    *,
    title,
    start_date,
    end_date,
    reg_deadline,
    description="",
    min_price=0,
    max_price=0,
) -> Event:
    if start_date >= end_date:
        raise ValidationError("start_date must be before end_date")
    if reg_deadline > start_date:
        raise ValidationError("reg_deadline must be on or before start_date")
    if min_price > max_price:
        raise ValidationError("min_price must not exceed max_price")
    return Event.objects.create(
        organizer=organizer,
        title=title,
        description=description,
        min_price=min_price,
        max_price=max_price,
        start_date=start_date,
        end_date=end_date,
        reg_deadline=reg_deadline,
    )


def _resolve_wishlist(user, wishlist_id):
    if wishlist_id is None:
        return None
    try:
        return Wishlist.objects.get(pk=wishlist_id, user=user)
    except Wishlist.DoesNotExist as exc:
        raise ValidationError("Wishlist not found or not owned by the user") from exc


def join_event(event: Event, user, wishlist_id=None) -> EventParticipant:
    if event.status != EventStatus.CREATED:
        raise ValidationError("Event is not open for registration")
    if timezone.now() > event.reg_deadline:
        raise ValidationError("Registration deadline has passed")
    if EventParticipant.objects.filter(event=event, user=user).exists():
        raise ValidationError("Already joined this event")
    wishlist = _resolve_wishlist(user, wishlist_id)
    return EventParticipant.objects.create(event=event, user=user, wishlist=wishlist)


def add_participant(event: Event, user, wishlist_id=None) -> EventParticipant:
    if event.status != EventStatus.CREATED:
        raise ValidationError("Participants can only be added before the draw")
    if EventParticipant.objects.filter(event=event, user=user).exists():
        raise ValidationError("User already participates")
    wishlist = _resolve_wishlist(user, wishlist_id)
    return EventParticipant.objects.create(event=event, user=user, wishlist=wishlist)


# назначения и перевод в active делаем одной транзакцией, иначе при сбое останемся без пар
@transaction.atomic
def run_draw(event: Event) -> None:
    if event.status != EventStatus.CREATED:
        raise ValidationError("Draw is only allowed from CREATED")
    user_ids = list(event.participants.values_list("user_id", flat=True))
    if len(user_ids) < 2:
        raise ValidationError("Need at least 2 participants to run the draw")

    pairs = assign_santas(user_ids)
    Assignment.objects.bulk_create(
        Assignment(event=event, santa_id=santa, ward_id=ward) for santa, ward in pairs.items()
    )
    transition(event, EventStatus.ACTIVE)


def complete_event(event: Event) -> None:
    _transition_or_400(event, EventStatus.COMPLETED)


def archive_event(event: Event) -> None:
    _transition_or_400(event, EventStatus.ARCHIVED)


def set_gift_sent(event: Event, user, sent: bool) -> EventParticipant:
    if event.status != EventStatus.ACTIVE:
        raise ValidationError("Gift status can only change while the event is active")
    try:
        participant = EventParticipant.objects.get(event=event, user=user)
    except EventParticipant.DoesNotExist as exc:
        raise ValidationError("You are not a participant of this event") from exc
    participant.gift_sent = sent
    participant.save(update_fields=["gift_sent"])
    return participant
