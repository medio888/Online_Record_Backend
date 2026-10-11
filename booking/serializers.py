from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Booking
from .slots import duration_limits, free_slots


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["student", "question", "date", "time", "duration"]

    def validate_question(self, question):
        if not question.is_active:
            raise serializers.ValidationError("Этот вопрос недоступен.")
        return question

    def validate_student(self, student):
        if student.bookings.filter(status="active", date__gte=timezone.localdate()).exists():
            raise serializers.ValidationError("У студента уже есть активная запись.")
        return student

    def validate(self, data):
        level = data["question"].level
        low, high = duration_limits(level)
        duration = data["duration"]
        if not low <= duration <= high or duration % 5 != 0:
            raise serializers.ValidationError(
                {"duration": f"Для этого вопроса от {low} до {high} минут, кратно 5."}
            )
        if data["time"] not in free_slots(level, data["date"], duration):
            raise serializers.ValidationError("Это время недоступно или пересекается с другой записью.")
        return data

    def create(self, validated_data):
        validated_data["level"] = validated_data["question"].level
        try:
            with transaction.atomic():
                return Booking.objects.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError("Это время только что заняли.")


class BookingTicketSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student", read_only=True)
    question_text = serializers.CharField(source="question.text", read_only=True)
    official = serializers.CharField(source="get_level_display", read_only=True)
    time = serializers.TimeField(format="%H:%M")
    end_time = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "code", "student_name", "question_text", "official",
            "date", "time", "end_time", "duration", "status", "created_at",
        ]

    def get_end_time(self, obj):
        start = datetime.combine(obj.date, obj.time)
        return (start + timedelta(minutes=obj.duration)).strftime("%H:%M")
