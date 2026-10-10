
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import QuestionCategory, Question, Appeal
from .serializers import (
    QuestionCategorySerializer,
    QuestionSerializer,
    AppealSerializer,
)


class QuestionCategoryListView(generics.ListAPIView):
    queryset = QuestionCategory.objects.filter(is_active=True)
    serializer_class = QuestionCategorySerializer
    permission_classes = [permissions.AllowAny]


class QuestionListView(generics.ListAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Question.objects.filter(
            is_active=True,
            category__is_active=True,
        ).select_related("category")

        level = self.request.query_params.get("level")
        category = self.request.query_params.get("category")

        if level is not None:
            if level not in ["1", "2", "3"]:
                return queryset.none()
            queryset = queryset.filter(level=int(level))

        if category is not None:
            if not category.isdigit():
                return queryset.none()
            queryset = queryset.filter(category_id=int(category))

        return queryset


class QuestionLevelListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        levels = [
            {"id": value, "title": title}
            for value, title in Question.Level.choices
        ]
        return Response(levels)


class AppealListCreateView(generics.ListCreateAPIView):
    serializer_class = AppealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Appeal.objects.select_related(
            "user", "question", "question__category"
        ).order_by("-created_at")

        # Сотрудникам с правами staff доступны все обращения.
        if self.request.user.is_staff:
            return queryset

        # Обычный пользователь видит только свои обращения.
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AppealDetailView(generics.RetrieveAPIView):
    serializer_class = AppealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Appeal.objects.select_related(
            "user", "question", "question__category"
        )

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(user=self.request.user)
