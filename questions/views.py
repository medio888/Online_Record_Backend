from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from config.pagination import StandardPagination

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
    pagination_class = StandardPagination

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



class AppealStatusUpdateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    ALLOWED_TRANSITIONS = {
        Appeal.Status.PENDING: {
            Appeal.Status.IN_PROGRESS,
            Appeal.Status.REJECTED,
        },
        Appeal.Status.IN_PROGRESS: {
            Appeal.Status.RESOLVED,
            Appeal.Status.REJECTED,
        },
        Appeal.Status.RESOLVED: set(),
        Appeal.Status.REJECTED: set(),
    }

    def patch(self, request, pk):
        appeal = get_object_or_404(
            Appeal.objects.select_related(
                "user", "question", "question__category"
            ),
            pk=pk,
        )

        new_status = request.data.get("status")

        valid_statuses = Appeal.Status.values
        if new_status not in valid_statuses:
            return Response(
                {
                    "status": (
                        "Недопустимый статус. Допустимые значения: "
                        + ", ".join(valid_statuses)
                    )
                },
                status=400,
            )

        allowed = self.ALLOWED_TRANSITIONS.get(
            appeal.status, set()
        )

        if new_status not in allowed:
            return Response(
                {
                    "status": (
                        f"Переход из «{appeal.status}» "
                        f"в «{new_status}» запрещён."
                    )
                },
                status=400,
            )

        appeal.status = new_status
        appeal.save(update_fields=["status", "updated_at"])

        return Response(AppealSerializer(appeal).data)
