from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.models import Assignment

from .consumers import OBSERVER, SANTA, WARD


def _label_for(assignment, sender_id) -> str:
    if sender_id == assignment.santa_id:
        return SANTA
    if sender_id == assignment.ward_id:
        return WARD
    return OBSERVER


class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=inline_serializer(
            name="ChatMessageOut",
            fields={
                "from": serializers.CharField(),
                "body": serializers.CharField(),
                "created_at": serializers.DateTimeField(),
            },
            many=True,
        )
    )
    def get(self, request, assignment_id):
        assignment = get_object_or_404(Assignment.objects.select_related("event"), id=assignment_id)
        is_member = request.user.id in (assignment.santa_id, assignment.ward_id)
        if not (is_member or request.user.role == "SUPERADMIN"):
            raise PermissionDenied("Not a member of this chat")

        data = [
            {
                "from": _label_for(assignment, m.sender_id),
                "body": m.body,
                "created_at": m.created_at,
            }
            for m in assignment.messages.all()
        ]
        return Response(data)
