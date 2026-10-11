import secrets

from django.db import models
from django.db.models import Q

from questions.models import Question
from student_registration.models import Student


def make_code():
    return secrets.token_hex(4).upper()


class Booking(models.Model):
    STATUSES = [
        ("active", "Активна"),
        ("cancelled", "Отменена"),
        ("done", "Проведена"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="bookings")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="bookings")
    level = models.PositiveSmallIntegerField(choices=Question.Level.choices)
    date = models.DateField()
    time = models.TimeField()
    duration = models.PositiveSmallIntegerField("Длительность, мин", default=10)
    code = models.CharField(max_length=8, unique=True, default=make_code)
    status = models.CharField(max_length=10, choices=STATUSES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time"]
        constraints = [
            models.UniqueConstraint(
                fields=["level", "date", "time"],
                condition=Q(status="active"),
                name="unique_active_slot",
            )
        ]

    def __str__(self):
        return f"{self.code}: {self.student} {self.date} {self.time:%H:%M}"
