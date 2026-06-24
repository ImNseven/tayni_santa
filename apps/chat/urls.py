from django.urls import path

from .views import ChatHistoryView

urlpatterns = [
    path(
        "chat/<uuid:assignment_id>/messages",
        ChatHistoryView.as_view(),
        name="chat-history",
    ),
]
