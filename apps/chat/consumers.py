import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.events.models import Assignment

from .models import ChatMessage

SANTA = "Санта"
WARD = "Подопечный"
OBSERVER = "Наблюдатель"


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        assignment_id = self.scope["url_route"]["kwargs"]["assignment_id"]
        self.assignment = await self._get_assignment(assignment_id)
        if self.assignment is None:
            await self.close()
            return

        is_member = self.user.id in (self.assignment.santa_id, self.assignment.ward_id)
        if not (is_member or self.user.role == "SUPERADMIN"):
            await self.close()
            return
        if self.assignment.event.status != "ACTIVE":
            await self.close()
            return

        self.group = f"chat_{self.assignment.id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data or "{}")
        body = (data.get("body") or "").strip()
        if not body:
            return
        # в базе храним реального отправителя, наружу отдаём только роль
        await self._save(self.assignment, self.user, body)
        await self.channel_layer.group_send(
            self.group,
            {"type": "chat.message", "label": self._label(), "body": body},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"from": event["label"], "body": event["body"]}))

    def _label(self) -> str:
        if self.user.id == self.assignment.santa_id:
            return SANTA
        if self.user.id == self.assignment.ward_id:
            return WARD
        return OBSERVER

    @database_sync_to_async
    def _get_assignment(self, assignment_id):
        try:
            return Assignment.objects.select_related("event").get(id=assignment_id)
        except Assignment.DoesNotExist:
            return None

    @database_sync_to_async
    def _save(self, assignment, user, body):
        return ChatMessage.objects.create(assignment=assignment, sender=user, body=body)
