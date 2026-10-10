from django.utils import timezone
from rest_framework import generics

from .models import Student, QueueTicket
from .serializers import StudentSerializer, QueueTicketSerializer


class StudentRegisterView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class QueueJoinView(generics.CreateAPIView):
    queryset = QueueTicket.objects.all()
    serializer_class = QueueTicketSerializer


class QueueListView(generics.ListAPIView):
    serializer_class = QueueTicketSerializer

    def get_queryset(self):
        qs = QueueTicket.objects.filter(
            date=timezone.localdate(), status__in=["waiting", "called"]
        )
        direction = self.request.query_params.get("direction")
        if direction:
            qs = qs.filter(direction=direction)
        return qs
