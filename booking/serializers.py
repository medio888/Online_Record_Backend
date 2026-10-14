from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Booking
from .slots import duration_limits, free_slots



class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["question", "date", "time", "duration"]

    def validate_question(self, question):
        if not question.is_active:
            raise serializers.ValidationError("Этот вопрос недоступен.")
        return question

    def validate(self, data):
        # Студент определяется сервером, а не клиентом.
        student = self.context.get("student")
        if student is None:
            raise serializers.ValidationError(
                "Не удалось определить профиль студента."
            )

        if student.bookings.filter(
            status="active",
            date__gte=timezone.localdate(),
        ).exists():
            raise serializers.ValidationError(
                "У студента уже есть активная запись."
            )

        level = data["question"].level
        low, high = duration_limits(level)
        duration = data["duration"]

        if not low <= duration <= high or duration % 5 != 0:
            raise serializers.ValidationError({
                "duration": (
                    f"Для этого вопроса от {low} до {high} минут, "
                    "кратно 5."
                )
            })

        if data["time"] not in free_slots(
            level,
            data["date"],
            duration,
        ):
            raise serializers.ValidationError(
                "Это время недоступно или пересекается с другой записью."
            )

        return data

    def create(self, validated_data):
        student = validated_data["student"]
        question = validated_data["question"]
        level = question.level
        day = validated_data["date"]
        start_time = validated_data["time"]
        duration = validated_data["duration"]

        start_min = start_time.hour * 60 + start_time.minute
        end_min = start_min + duration

        try:
            with transaction.atomic():
                # Блокируем профиль: один студент не сможет
                # одновременно создать две активные записи.
                student.__class__.objects.select_for_update().get(
                    pk=student.pk
                )

                # Все бронирования одного уровня используют
                # одну и ту же блокировку.
                lock_question = (
                    question.__class__.objects
                    .select_for_update()
                    .filter(level=level)
                    .order_by("pk")
                    .first()
                )

                if lock_question is None:
                    raise serializers.ValidationError(
                        "Для этого уровня нет доступных вопросов."
                    )

                # Проверяем актуальность вопроса уже под блокировкой.
                question.refresh_from_db()

                if not question.is_active:
                    raise serializers.ValidationError(
                        {"question": "Этот вопрос недоступен."}
                    )

                # Повторно проверяем активную запись студента.
                if student.bookings.filter(
                    status="active",
                    date__gte=timezone.localdate(),
                ).exists():
                    raise serializers.ValidationError(
                        "У студента уже есть активная запись."
                    )

                # Повторно проверяем доступность времени.
                if start_time not in free_slots(level, day, duration):
                    raise serializers.ValidationError(
                        "Это время уже занято или недоступно."
                    )

                validated_data["level"] = level

                return Booking.objects.create(**validated_data)

        except IntegrityError:
            raise serializers.ValidationError(
                "Это время только что заняли. Выберите другое."
            )



class BookingTicketSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student", read_only=True)
    question_text = serializers.CharField(source="question.text", read_only=True)
    official = serializers.CharField(source="get_level_display", read_only=True)
    time = serializers.TimeField(format="%H:%M")
    end_time = serializers.SerializerMethodField()
    ahead = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "code", "student_name", "question_text", "official",
            "date", "time", "end_time", "duration", "ahead", "status", "created_at",
        ]

    def get_end_time(self, obj):
        start = datetime.combine(obj.date, obj.time)
        return (start + timedelta(minutes=obj.duration)).strftime("%H:%M")

    def get_ahead(self, obj):
        return Booking.objects.filter(
            level=obj.level, date=obj.date, status="active", time__lt=obj.time
        ).count()
