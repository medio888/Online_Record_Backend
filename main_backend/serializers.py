import re

from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers

from .models import Student, QueueTicket

NAME_RE = re.compile(r"^[^\W\d_]+(?:[ \-'][^\W\d_]+)*$")
PHONE_RE = re.compile(r"^\+?\d{9,15}$")


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "id", "first_name", "last_name", "phone",
            "direction", "course", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def _check_name(self, value):
        if not NAME_RE.match(value):
            raise serializers.ValidationError(
                "Допустимы только буквы, пробел и дефис."
            )
        return value

    def validate_first_name(self, value):
        return self._check_name(value)

    def validate_last_name(self, value):
        return self._check_name(value)

    def validate_phone(self, value):
        cleaned = re.sub(r"[\s\-()]", "", value)
        if not PHONE_RE.match(cleaned):
            raise serializers.ValidationError(
                "Введите номер в международном формате, например +996555123456."
            )
        return cleaned

    def validate_course(self, value):
        if not 1 <= value <= 3:
            raise serializers.ValidationError("Курс должен быть от 1 до 3.")
        return value


class QueueTicketSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student", read_only=True)

    class Meta:
        model = QueueTicket
        fields = [
            "id", "student", "student_name", "direction",
            "number", "date", "status", "created_at",
        ]
        read_only_fields = ["direction", "number", "date", "status", "created_at"]

    def validate_student(self, student):
        if student.tickets.filter(status__in=["waiting", "called"]).exists():
            raise serializers.ValidationError("Студент уже стоит в очереди.")
        return student

    def create(self, validated_data):
        student = validated_data["student"]
        today = timezone.localdate()
        with transaction.atomic():
            last = (
                QueueTicket.objects.filter(direction=student.direction, date=today)
                .aggregate(m=Max("number"))["m"] or 0
            )
            return QueueTicket.objects.create(
                student=student,
                direction=student.direction,
                date=today,
                number=last + 1,
            )


class QueueStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueueTicket
        fields = ["status"]