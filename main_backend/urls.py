from django.urls import path
from .views import StudentRegisterView, QueueJoinView, QueueListView

urlpatterns = [
    path("register/", StudentRegisterView.as_view(), name="student-register"),
    path("queue/join/", QueueJoinView.as_view(), name="queue-join"),
    path("queue/", QueueListView.as_view(), name="queue-list"),
]