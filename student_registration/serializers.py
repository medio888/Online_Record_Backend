import re

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from rest_framework import serializers

from .models import Student, QueueTicket


User = get_user_model()

NAME_RE = re.compile(r"^[^\W\d_]+(?:[ -][^\W\d_]+)*$")


class StudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        write_only=True,
        max_length=150,
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )
    phone = serializers.CharField(max_length=20)

    class Meta:
        model = Student
        fields = [
            "id",
            "username",
            "password",
            "first_name",
            "last_name",
            "phone",
            "direction",
            "course",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким логином уже существует."
            )
        return value

    def _check_name(self, value):
        value = value.strip()

        if not NAME_RE.fullmatch(value):
            raise serializers.ValidationError(
                "Допустимы только буквы, пробел и дефис."
            )

        return value

    def validate_first_name(self, value):
        return self._check_name(value)

    def validate_last_name(self, value):
        return self._check_name(value)

    def validate_phone(self, value):
        digits = re.sub(r"\D", "", value)

        if digits.startswith("996"):
            digits = digits[3:]
        elif digits.startswith("0"):
            digits = digits[1:]

        if len(digits) != 9:
            raise serializers.ValidationError(
                "Номер должен быть в формате +996XXXXXXXXX."
            )

        return "+996" + digits

    def validate_course(self, value):
        if value not in (1, 2, 3):
            raise serializers.ValidationError(
                "Курс должен быть от 1 до 3."
            )

        return value

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop("username")
        password = validated_data.pop("password")

        user = User.objects.create_user(
            username=username,
            password=password,
        )

        student = Student.objects.create(
            user=user,
            **validated_data,
        )

        return student


class QueueTicketSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student",
        read_only=True,
    )

    class Meta:
        model = QueueTicket
        fields = [
            "id",
            "student",
            "student_name",
            "direction",
            "number",
            "date",
            "status",
            "created_at",
            "called_at",
            "completed_at",
            "cancelled_at",
        ]
        read_only_fields = [
            "id",
            "student",
            "direction",
            "number",
            "date",
            "status",
            "created_at",
            "called_at",
            "completed_at",
            "cancelled_at",
        ]

    def validate(self, attrs):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Для постановки в очередь необходимо войти."
            )

        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            raise serializers.ValidationError(
                "У этой учётной записи нет профиля студента."
            )

        if student.tickets.filter(
            status__in=["waiting", "called"]
        ).exists():
            raise serializers.ValidationError(
                "Студент уже стоит в очереди."
            )

        attrs["student"] = student
        return attrs

    def create(self, validated_data):
        student = validated_data["student"]
        today = timezone.localdate()

        with transaction.atomic():
            last = (
                QueueTicket.objects.filter(
                    direction=student.direction,
                    date=today,
                ).aggregate(m=Max("number"))["m"] or 0
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
        fields = [
            "status",
            "called_at",
            "completed_at",
            "cancelled_at",
        ]
        read_only_fields = [
            "called_at",
            "completed_at",
            "cancelled_at",
        ]

    def validate_status(self, new_status):
        ticket = self.instance

        if ticket is None:
            return new_status

        allowed_transitions = {
            "waiting": {"cancelled"},
            "called": {"done", "cancelled"},
            "done": set(),
            "cancelled": set(),
        }

        if new_status not in allowed_transitions[ticket.status]:
            raise serializers.ValidationError(
                f"Недопустимый переход: "
                f"{ticket.status} -> {new_status}."
            )

        return new_status

    def update(self, instance, validated_data):
        new_status = validated_data["status"]
        now = timezone.now()

        instance.status = new_status

        if new_status == "done":
            instance.completed_at = now

        elif new_status == "cancelled":
            instance.cancelled_at = now

        instance.save()
        return instance