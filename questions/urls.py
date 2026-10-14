
from django.urls import path

from .views import (
    QuestionCategoryListView,
    QuestionListView,
    QuestionLevelListView,
    AppealListCreateView,
    AppealDetailView,
    AppealStatusUpdateView,
)

urlpatterns = [
    path(
        "categories/",
        QuestionCategoryListView.as_view(),
        name="question-categories",
    ),
    path(
        "",
        QuestionListView.as_view(),
        name="question-list",
    ),
    path(
        "levels/",
        QuestionLevelListView.as_view(),
        name="question-levels",
    ),
    path(
        "appeals/",
        AppealListCreateView.as_view(),
        name="appeal-list-create",
    ),
    path(
        "appeals/<int:pk>/",
        AppealDetailView.as_view(),
        name="appeal-detail",
    ),
    path(
        "appeals/<int:pk>/status/",
        AppealStatusUpdateView.as_view(),
        name="appeal-status-update",
    ),
]
