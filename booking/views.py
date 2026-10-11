from datetime import date as date_cls

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        return Response(BookingTicketSerializer(booking).data, status=201)


class TicketView(generics.RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingTicketSerializer
    lookup_field = "code"
