from django.urls import path

from .consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<uuid:assignment_id>", ChatConsumer.as_asgi()),
]
