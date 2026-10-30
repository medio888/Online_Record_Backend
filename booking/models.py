
import secrets

from django.db import models
from django.db.models import Q

from questions.models import Question
from student_registration.models import Student
from calendar_for_admin.models import ScheduleRule


def make_code():
    return secrets.token_hex(4).upper()


class Booking(models.Model):
    STATUSES = [
        ("active", "Активна"),
        ("cancelled", "Отменена"),
        ("done", "Проведена"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    schedule_rule = models.ForeignKey(
        ScheduleRule,
        on_delete=models.PROTECT,
        related_name="student_bookings",
        null=True,
        blank=True,
        verbose_name="Расписание сотрудника",
    )
    level = models.PositiveSmallIntegerField(
        choices=Question.Level.choices,
    )
    date = models.DateField()
    time = models.TimeField()
    duration = models.PositiveSmallIntegerField(
        "Длительность, мин",
        default=10,
    )
    code = models.CharField(
        max_length=8,
        unique=True,
        default=make_code,
    )
    status = models.CharField(
        max_length=10,
        choices=STATUSES,
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time"]
        constraints = [
            models.UniqueConstraint(
                fields=["schedule_rule", "date", "time"],
                condition=Q(
                    status="active",
                    schedule_rule__isnull=False,
                ),
                name="unique_active_schedule_slot",
            ),
        ]

    def __str__(self):
        return (
            f"{self.code}: {self.student} "
            f"{self.date} {self.time:%H:%M}"
        )
