
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework import serializers

from .models import Booking
from .slots import duration_limits, free_slot_rules


User = get_user_model()


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["question", "date", "time", "duration"]

    def validate_question(self, question):
        if not question.is_active:
            raise serializers.ValidationError(
                "Этот вопрос недоступен."
            )

        if question.responsible is None:
            raise serializers.ValidationError(
                "Для этого вопроса не назначен ответственный сотрудник."
            )

        return question

    def validate(self, data):
        student = self.context.get("student")

        if student is None:
            raise serializers.ValidationError(
                "Не удалось определить профиль студента."
            )

        if data["date"] < timezone.localdate():
            raise serializers.ValidationError({
                "date": "Нельзя записаться на прошедшую дату."
            })

        if student.bookings.filter(
            status="active",
            date__gte=timezone.localdate(),
        ).exists():
            raise serializers.ValidationError(
                "У студента уже есть активная запись."
            )

        question = data["question"]
        low, high = duration_limits(question.level)
        duration = data["duration"]

        if not low <= duration <= high or duration % 5 != 0:
            raise serializers.ValidationError({
                "duration": (
                    f"Для этого вопроса от {low} до {high} минут, "
                    "кратно 5."
                )
            })

        available = [
            slot_time
            for slot_time, rule in free_slot_rules(
                question,
                data["date"],
                duration,
            )
        ]

        if data["time"] not in available:
            raise serializers.ValidationError(
                "Это время недоступно или пересекается с другой записью."
            )

        return data

    def create(self, validated_data):
        student = validated_data["student"]
        question = validated_data["question"]
        day = validated_data["date"]
        start_time = validated_data["time"]
        duration = validated_data["duration"]

        try:
            with transaction.atomic():
                # Блокируем профиль студента.
                student.__class__.objects.select_for_update().get(
                    pk=student.pk
                )

                # Повторно получаем актуальный вопрос.
                question = (
                    question.__class__.objects
                    .select_related("responsible")
                    .get(pk=question.pk)
                )

                if not question.is_active:
                    raise serializers.ValidationError({
                        "question": "Этот вопрос недоступен."
                    })

                if question.responsible is None:
                    raise serializers.ValidationError({
                        "question": "Не назначен ответственный сотрудник."
                    })

                # Общая блокировка сотрудника для Booking и Appointment.
                User.objects.select_for_update().get(
                    pk=question.responsible_id
                )

                if student.bookings.filter(
                    status="active",
                    date__gte=timezone.localdate(),
                ).exists():
                    raise serializers.ValidationError(
                        "У студента уже есть активная запись."
                    )

                # Повторно проверяем доступность времени.
                available = free_slot_rules(
                    question,
                    day,
                    duration,
                )

                selected_rule = next(
                    (
                        rule
                        for slot_time, rule in available
                        if slot_time == start_time
                    ),
                    None,
                )

                if selected_rule is None:
                    raise serializers.ValidationError(
                        "Это время уже занято или недоступно."
                    )

                return Booking.objects.create(
                    student=student,
                    question=question,
                    schedule_rule=selected_rule,
                    level=question.level,
                    date=day,
                    time=start_time,
                    duration=duration,
                )

        except IntegrityError:
            raise serializers.ValidationError(
                "Это время только что заняли. Выберите другое."
            )


class BookingTicketSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student",
        read_only=True,
    )

    question_text = serializers.CharField(
        source="question.text",
        read_only=True,
    )

    official = serializers.CharField(
        source="get_level_display",
        read_only=True,
    )

    time = serializers.TimeField(format="%H:%M")
    end_time = serializers.SerializerMethodField()
    ahead = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "code",
            "student_name",
            "question_text",
            "official",
            "date",
            "time",
            "end_time",
            "duration",
            "ahead",
            "status",
            "created_at",
        ]

    def get_end_time(self, obj):
        start = datetime.combine(obj.date, obj.time)

        return (
            start + timedelta(minutes=obj.duration)
        ).strftime("%H:%M")

    def get_ahead(self, obj):
        return Booking.objects.filter(
            level=obj.level,
            date=obj.date,
            status="active",
            time__lt=obj.time,
        ).count()
