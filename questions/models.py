
from django.conf import settings
from django.db import models


class QuestionCategory(models.Model):
    title = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Question(models.Model):

    class Level(models.IntegerChoices):
        DEAN = 1, "Деканат"
        DEPUTY_DIRECTOR = 2, "Заместитель директора"
        DIRECTOR = 3, "Директор"

    category = models.ForeignKey(
        QuestionCategory,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.CharField(max_length=500)
    level = models.PositiveSmallIntegerField(
        choices=Level.choices,
        default=Level.DEAN,
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.text


class Appeal(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает рассмотрения"
        IN_PROGRESS = "in_progress", "Рассматривается"
        RESOLVED = "resolved", "Решено"
        REJECTED = "rejected", "Отклонено"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appeals",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="appeals",
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Обращение #{self.pk} — {self.user}"
