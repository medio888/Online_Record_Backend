from datetime import date as date_cls

from django.utils import timezone

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from student_registration.models import Student

from questions.models import Question

from .models import Booking
from .serializers import BookingCreateSerializer, BookingTicketSerializer
from .slots import duration_limits, free_slots


def get_question(request):
    try:
        pk = int(request.query_params.get("question", ""))
    except ValueError:
        return None
    return get_object_or_404(Question, pk=pk, is_active=True)


class RouteView(APIView):
    def get(self, request):
        question = get_question(request)
        if question is None:
            return Response({"question": "Укажите id вопроса."}, status=400)
        low, high = duration_limits(question.level)
        return Response({
            "question": question.text,
            "level": question.level,
            "official": question.get_level_display(),
            "min_duration": low,
            "max_duration": high,
        })


class SlotsView(APIView):
    def get(self, request):
        question = get_question(request)
        if question is None:
            return Response({"question": "Укажите id вопроса."}, status=400)
        try:
            day = date_cls.fromisoformat(request.query_params.get("date", ""))
        except ValueError:
            return Response({"date": "Формат даты: ГГГГ-ММ-ДД."}, status=400)
        if day < timezone.localdate():
            return Response(
                {"date": "Нельзя выбрать прошедшую дату."},
                status=400,
            )

        low, high = duration_limits(question.level)
        try:
            duration = int(request.query_params.get("duration", low))
        except ValueError:
            return Response({"duration": "Укажите число минут."}, status=400)
        if not low <= duration <= high or duration % 5 != 0:
            return Response(
                {"duration": f"Для этого вопроса от {low} до {high} минут, кратно 5."},
                status=400,
            )

        slots = [t.strftime("%H:%M") for t in free_slots(question.level, day, duration)]
        return Response({
            "official": question.get_level_display(),
            "date": day.isoformat(),
            "duration": duration,
            "slots": slots,
        })



class BookingCreateView(generics.CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Получаем профиль студента из авторизованного аккаунта.
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {"detail": "У аккаунта нет профиля студента."},
                status=403,
            )

        serializer = self.get_serializer(data=request.data)

        # Передаём профиль сервером для проверки активных записей.
        serializer.context["student"] = student

        serializer.is_valid(raise_exception=True)

        # Владелец записи назначается только сервером.
        booking = serializer.save(student=student)

        return Response(
            BookingTicketSerializer(booking).data,
            status=201,
        )




class TicketView(generics.RetrieveAPIView):
    serializer_class = BookingTicketSerializer
    lookup_field = "code"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Booking.objects.select_related(
            "student",
            "question",
        )

        # Сотрудники могут просматривать записи
        # в рамках своих полномочий.
        if self.request.user.is_staff:
            return queryset

        # Обычный пользователь видит только свои записи.
        try:
            student = self.request.user.student_profile
        except Student.DoesNotExist:
            return queryset.none()

        return queryset.filter(student=student)




class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # Определяем студента по аккаунту, а не по student_id из запроса.
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {"detail": "У аккаунта нет профиля студента."},
                status=403,
            )

        with transaction.atomic():
            # Ищем запись только среди записей этого студента.
            # Чужая запись будет выглядеть как несуществующая.
            booking = get_object_or_404(
                Booking.objects.select_for_update(),
                pk=pk,
                student=student,
            )

            if booking.status == "cancelled":
                return Response({
                    "detail": "Запись уже отменена.",
                    "booking": BookingTicketSerializer(booking).data,
                }, status=200)

            if booking.status != "active":
                return Response(
                    {"detail": "Можно отменить только активную запись."},
                    status=400,
                )

            booking.status = "cancelled"
            booking.save(update_fields=["status"])

        return Response({
            "detail": "Запись отменена.",
            "booking": BookingTicketSerializer(booking).data,
        }, status=200)
