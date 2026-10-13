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

        valid_directions = dict(Student.DIRECTIONS)

        if direction not in valid_directions:
            return Response(
                {"direction": "Указано неизвестное направление."},
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
        ticket.called_at = timezone.now()
        ticket.save(update_fields=["status", "called_at"])

        return Response(QueueTicketSerializer(ticket).data)


class QueueTicketUpdateView(generics.UpdateAPIView):
    queryset = QueueTicket.objects.all()
    serializer_class = QueueStatusSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ["patch"]


class ReceptionScreenView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        direction = request.query_params.get("direction")

        if not direction:
            return Response(
                {"direction": "Укажите направление, например it."},
                status=400,
            )

        valid_directions = dict(Student.DIRECTIONS)

        if direction not in valid_directions:
            return Response(
                {"direction": "Указано неизвестное направление."},
                status=400,
            )

        today = timezone.localdate()

        tickets = QueueTicket.objects.filter(
            date=today,
            direction=direction,
        ).select_related("student")

        # Текущий посетитель
        current_ticket = (
            tickets.filter(status="called")
            .order_by("called_at", "number")
            .first()
        )

        # Следующий посетитель
        next_ticket = (
            tickets.filter(status="waiting")
            .order_by("number")
            .first()
        )

        # История завершённых приёмов за сегодня
        history_tickets = (
            tickets.filter(
                status="done",
                called_at__isnull=False,
                completed_at__isnull=False,
            )
            .order_by("-completed_at")
        )

        current_visitor = self.serialize_ticket(current_ticket)
        next_visitor = self.serialize_ticket(next_ticket)

        history = []

        for ticket in history_tickets:
            item = self.serialize_ticket(ticket)

            duration = (
                ticket.completed_at - ticket.called_at
            ).total_seconds() / 60

            item["duration_minutes"] = round(duration, 2)
            history.append(item)

        return Response({
            "date": today,
            "direction": direction,
            "direction_name": valid_directions[direction],
            "current_visitor": current_visitor,
            "next_visitor": next_visitor,
            "history": history,
        })

    @staticmethod
    def serialize_ticket(ticket):
        if ticket is None:
            return None

        return {
            "id": ticket.id,
            "number": ticket.number,
            "student_name": (
                f"{ticket.student.first_name} "
                f"{ticket.student.last_name}"
            ),
            "direction": ticket.direction,
            "status": ticket.status,
            "created_at": ticket.created_at,
            "called_at": ticket.called_at,
            "completed_at": ticket.completed_at,
            "cancelled_at": ticket.cancelled_at,
        }