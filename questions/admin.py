
from django.contrib import admin
from .models import QuestionCategory, Question, Appeal


@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_active")
    search_fields = ("title",)
    list_filter = ("is_active",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "category", "level", "responsible", "is_active")
    list_filter = ("level", "category", "is_active")
    search_fields = ("text",)


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "question",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "message",
        "user__username",
        "question__text",
    )
    readonly_fields = ("created_at", "updated_at")
