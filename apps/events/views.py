from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import HasPermission, IsOwnerOrSuperadmin, Permission

from . import services
from .models import Assignment, Event, EventParticipant
from .serializers import (
    AddParticipantSerializer,
    EventSerializer,
    GiftSentSerializer,
    JoinSerializer,
    MyAssignmentSerializer,
    ParticipantSerializer,
)

User = get_user_model()

_STATUS_FILTERS = {
    "active": "ACTIVE",
    "past": "COMPLETED",
    "completed": "COMPLETED",
    "archived": "ARCHIVED",
    "created": "CREATED",
}


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    owner_field = "organizer_id"

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), HasPermission(Permission.MANAGE_EVENTS)()]
        if self.action in ("update", "partial_update", "destroy"):
            return [
                IsAuthenticated(),
                HasPermission(Permission.MANAGE_EVENTS)(),
                IsOwnerOrSuperadmin(),
            ]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Event.objects.all()
        if getattr(self, "swagger_fake_view", False):
            return qs
        wanted = self.request.query_params.get("status")
        if wanted and wanted.lower() in _STATUS_FILTERS:
            qs = qs.filter(status=_STATUS_FILTERS[wanted.lower()])
        return qs

    def perform_create(self, serializer):
        event = services.create_event(self.request.user, **serializer.validated_data)
        serializer.instance = event

    def _require_organizer(self, event):
        if self.request.user.role != "SUPERADMIN" and event.organizer_id != self.request.user.id:
            raise PermissionDenied("Only the organizer can perform this action")

    @extend_schema(request=JoinSerializer, responses={201: ParticipantSerializer})
    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        event = self.get_object()
        serializer = JoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = services.join_event(
            event, request.user, serializer.validated_data.get("wishlist_id")
        )
        return Response(ParticipantSerializer(participant).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=AddParticipantSerializer, responses={201: ParticipantSerializer})
    @action(detail=True, methods=["post"])
    def participants(self, request, pk=None):
        event = self.get_object()
        self._require_organizer(event)
        serializer = AddParticipantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target = get_object_or_404(User, pk=serializer.validated_data["user_id"])
        participant = services.add_participant(
            event, target, serializer.validated_data.get("wishlist_id")
        )
        return Response(ParticipantSerializer(participant).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=GiftSentSerializer, responses={200: ParticipantSerializer})
    @action(detail=True, methods=["post"], url_path="gift-sent")
    def gift_sent(self, request, pk=None):
        event = self.get_object()
        serializer = GiftSentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = services.set_gift_sent(
            event, request.user, serializer.validated_data["gift_sent"]
        )
        return Response(ParticipantSerializer(participant).data)

    @extend_schema(responses={200: MyAssignmentSerializer})
    @action(detail=True, methods=["get"], url_path="my-assignment")
    def my_assignment(self, request, pk=None):
        event = self.get_object()
        assignment = get_object_or_404(Assignment, event=event, santa=request.user)
        ward_participation = EventParticipant.objects.filter(
            event=event, user=assignment.ward
        ).first()
        data = {
            "ward_phone": assignment.ward.phone,
            "ward_wishlist": ward_participation.wishlist if ward_participation else None,
        }
        return Response(MyAssignmentSerializer(data).data)

    @extend_schema(request=None, responses={200: EventSerializer})
    @action(detail=True, methods=["post"])
    def draw(self, request, pk=None):
        event = self.get_object()
        self._require_organizer(event)
        services.run_draw(event)
        return Response(EventSerializer(event).data)

    @extend_schema(request=None, responses={200: EventSerializer})
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        event = self.get_object()
        self._require_organizer(event)
        services.complete_event(event)
        return Response(EventSerializer(event).data)

    @extend_schema(request=None, responses={200: EventSerializer})
    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        event = self.get_object()
        self._require_organizer(event)
        services.archive_event(event)
        return Response(EventSerializer(event).data)
