from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class Student(models.Model):
    DIRECTIONS = [
        ("it", "IT"),
        ("business_analytics", "Бизнес-аналитика"),
        ("translator_english", "Переводчики английского"),
        ("translator_korean", "Переводчики корейского"),
        ("law", "Юристы"),
        ("marketing", "Маркетологи"),
        ("design", "Дизайнеры"),
    ]

    COURSES = [
        (1, "1 курс"),
        (2, "2 курс"),
        (3, "3 курс"),
    ]

    first_name = models.CharField("Имя", max_length=50)
    last_name = models.CharField("Фамилия", max_length=50)
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
        verbose_name="Учётная запись",
    )
    phone = models.CharField(
        "Телефон",
        max_length=13,
        validators=[
            RegexValidator(
                regex=r"^\+996\d{9}$",
                message="Формат: +996XXXXXXXXX (9 цифр после 996).",
            )
        ],
    )

    direction = models.CharField("Направление", max_length=30, choices=DIRECTIONS)
    course = models.PositiveSmallIntegerField("Курс", choices=COURSES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class QueueTicket(models.Model):
    STATUSES = [
        ("waiting", "Ждёт"),
        ("called", "Вызван"),
        ("done", "Принят"),
        ("cancelled", "Отменён"),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="tickets"
    )
    direction = models.CharField(max_length=30, choices=Student.DIRECTIONS)
    number = models.PositiveIntegerField()
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=STATUSES, default="waiting")
    created_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(
        "Время вызова",
        null=True,
        blank=True,
    )
    completed_at = models.DateTimeField(
        "Время завершения",
        null=True,
        blank=True,
    )
    cancelled_at = models.DateTimeField(
        "Время отмены",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["date", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["direction", "date", "number"],
                name="unique_ticket_number",
            )
        ]

    def __str__(self):
        return f"{self.direction} №{self.number} ({self.student})"