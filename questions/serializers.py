
from rest_framework import serializers
from .models import QuestionCategory, Question, Appeal


class QuestionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCategory
        fields = ["id", "title", "description"]


class QuestionSerializer(serializers.ModelSerializer):
    category_title = serializers.CharField(
        source="category.title",
        read_only=True,
    )
    level_display = serializers.CharField(
        source="get_level_display",
        read_only=True,
    )

    class Meta:
        model = Question
        fields = [
            "id",
            "category",
            "category_title",
            "text",
            "level",
            "level_display",
        ]


class AppealSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(
        source="question.text",
        read_only=True,
    )
    level = serializers.IntegerField(
        source="question.level",
        read_only=True,
    )
    level_display = serializers.CharField(
        source="question.get_level_display",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = Appeal
        fields = [
            "id",
            "question",
            "question_text",
            "level",
            "level_display",
            "message",
            "status",
            "status_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_question(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "Этот вопрос больше недоступен."
            )

        if not value.category.is_active:
            raise serializers.ValidationError(
                "Категория этого вопроса неактивна."
            )

        return value
