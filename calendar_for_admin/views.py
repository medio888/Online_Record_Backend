
from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ScheduleRule, Appointment
from .serializers import (
    ScheduleRuleSerializer,
    AppointmentSerializer,
)


BOOKING_HORIZON_DAYS = 30


def generate_slots(rule, appointment_date):
    """Создаёт список сеансов для конкретной даты и правила."""
    duration = timedelta(minutes=rule.slot_duration_minutes)

    current = datetime.combine(
        appointment_date,
        rule.start_time,
    )
    finish = datetime.combine(
        appointment_date,
        rule.end_time,
    )

    slots = []

    while current + duration <= finish:
        slot_start = current.time()
        slot_end = (current + duration).time()

        slots.append({
            "start_time": slot_start,
            "end_time": slot_end,
        })

        current += duration

    return slots


class AvailabilityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        today = timezone.localdate()
        last_date = today + timedelta(
            days=BOOKING_HORIZON_DAYS - 1
        )

        rules = ScheduleRule.objects.filter(
            is_active=True,
        ).select_related("administrator")

        result = []
        current_date = today

        while current_date <= last_date:
            daily_slots = []

            day_rules = rules.filter(
                weekday=current_date.weekday(),
            )

            for rule in day_rules:
                for slot in generate_slots(rule, current_date):
                    if (
                        current_date == today
                        and slot["start_time"]
                        <= timezone.localtime().time().replace(
                            tzinfo=None
                        )
                    ):
                        continue

                    already_booked = Appointment.objects.filter(
                        schedule_rule=rule,
                        appointment_date=current_date,
                        start_time=slot["start_time"],
                        status="booked",
                    ).exists()

                    if already_booked:
                        continue

                    daily_slots.append({
                        "schedule_rule": rule.id,
                        "administrator": rule.administrator_id,
                        "start_time": slot["start_time"].strftime(
                            "%H:%M"
                        ),
                        "end_time": slot["end_time"].strftime(
                            "%H:%M"
                        ),
                    })

            if daily_slots:
                result.append({
                    "date": current_date.isoformat(),
                    "weekday": current_date.weekday(),
                    "slots": daily_slots,
                })

            current_date += timedelta(days=1)

        return Response({
            "timezone": "Asia/Bishkek",
            "booking_horizon_days": BOOKING_HORIZON_DAYS,
            "from_date": today.isoformat(),
            "to_date": last_date.isoformat(),
            "available_dates": result,
        })


class ScheduleRuleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleRuleSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = ScheduleRule.objects.select_related(
            "administrator"
        )

        if self.request.user.is_superuser:
            return queryset

        return queryset.filter(
            administrator=self.request.user
        )


class AppointmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Appointment.objects.select_related(
            "schedule_rule",
            "schedule_rule__administrator",
        )

        if self.request.user.is_superuser:
            return queryset

        return queryset.filter(
            schedule_rule__administrator=self.request.user
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        appointment = self.get_object()

        if appointment.status == "cancelled":
            return Response({
                "detail": "Запись уже отменена."
            })

        appointment.status = "cancelled"
        appointment.save(update_fields=["status"])

        return Response({
            "detail": "Запись отменена.",
            "appointment_id": appointment.id,
            "status": appointment.status,
        })


class AppointmentBookingView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                appointment = serializer.save()
        except IntegrityError:
            return Response(
                {
                    "detail":
                        "Этот сеанс уже забронировал другой пользователь. "
                        "Обновите список свободного времени."
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )
