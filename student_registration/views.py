
from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Student, QueueTicket
from .serializers import (
    StudentSerializer,
    QueueTicketSerializer,
    QueueStatusSerializer,
)


class StudentRegisterView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [AllowAny]


class QueueJoinView(generics.CreateAPIView):
    queryset = QueueTicket.objects.all()
    serializer_class = QueueTicketSerializer


class QueueListView(generics.ListAPIView):
    serializer_class = QueueTicketSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = QueueTicket.objects.filter(
            date=timezone.localdate(),
            status__in=["waiting", "called"],
        )

        direction = self.request.query_params.get("direction")
        if direction:
            qs = qs.filter(direction=direction)

        return qs


class QueueCallNextView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        direction = request.query_params.get("direction")

        if not direction:
            return Response(
                {"direction": "Укажите направление."},
                status=400,
            )

        ticket = (
            QueueTicket.objects.filter(
                date=timezone.localdate(),
                direction=direction,
                status="waiting",
            )
            .order_by("number")
            .first()
        )

        if ticket is None:
            return Response(
                {"detail": "В очереди никого нет."},
                status=404,
            )

        ticket.status = "called"
        ticket.save(update_fields=["status"])

        return Response(QueueTicketSerializer(ticket).data)


class QueueTicketUpdateView(generics.UpdateAPIView):
    queryset = QueueTicket.objects.all()
    serializer_class = QueueStatusSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ["patch"]
