from django.urls import path
from .views import (
    StudentRegisterView,
    QueueJoinView,
    QueueListView,
    QueueCallNextView,
    QueueTicketUpdateView,
)

urlpatterns = [
    path("register/", StudentRegisterView.as_view(), name="student-register"),
    path("queue/join/", QueueJoinView.as_view(), name="queue-join"),
    path("queue/call-next/", QueueCallNextView.as_view(), name="queue-call-next"),
    path("queue/<int:pk>/", QueueTicketUpdateView.as_view(), name="queue-update"),
    path("queue/", QueueListView.as_view(), name="queue-list"),
]
