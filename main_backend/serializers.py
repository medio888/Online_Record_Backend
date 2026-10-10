import re
from rest_framework import serializers
from .models import Student

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