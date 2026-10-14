
from django.conf import settings
from django.db import models
from django.db.models import Q


class ScheduleRule(models.Model):
    WEEKDAYS = [
        (0, "Понедельник"),
        (1, "Вторник"),
        (2, "Среда"),
        (3, "Четверг"),
        (4, "Пятница"),
        (5, "Суббота"),
        (6, "Воскресенье"),
    ]

    administrator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="or_schedule_rules",
        verbose_name="Администратор",
    )

    weekday = models.PositiveSmallIntegerField(
        choices=WEEKDAYS,
        verbose_name="День недели",
    )

    start_time = models.TimeField(
        verbose_name="Начало приёма",
    )

    end_time = models.TimeField(
        verbose_name="Конец приёма",
    )

    slot_duration_minutes = models.PositiveSmallIntegerField(
        default=30,
        verbose_name="Длительность сеанса (минуты)",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Расписание активно",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        ordering = ["weekday", "start_time"]
        verbose_name = "Правило расписания"
        verbose_name_plural = "Правила расписания"

    def __str__(self):
        return (
            f"{self.administrator.username} — "
            f"{self.get_weekday_display()}, "
            f"{self.start_time.strftime('%H:%M')}-"
            f"{self.end_time.strftime('%H:%M')}"
        )


class Appointment(models.Model):
    STATUSES = [
        ("booked", "Забронировано"),
        ("cancelled", "Отменено"),
    ]

    schedule_rule = models.ForeignKey(
        ScheduleRule,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Правило расписания",
    )

    appointment_date = models.DateField(
        verbose_name="Дата приёма",
    )

    start_time = models.TimeField(
        verbose_name="Начало сеанса",
    )

    end_time = models.TimeField(
        verbose_name="Конец сеанса",
    )

    visitor_name = models.CharField(
        max_length=100,
        verbose_name="Имя посетителя",
    )

    visitor_phone = models.CharField(
        max_length=20,
        verbose_name="Телефон посетителя",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUSES,
        default="booked",
        verbose_name="Статус записи",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата бронирования",
    )
    
    administrator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="or_appointments",
        editable=False,
    )

    class Meta:
        ordering = ["appointment_date", "start_time"]
        verbose_name = "Запись на приём"
        verbose_name_plural = "Записи на приём"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "schedule_rule",
                    "appointment_date",
                    "start_time",
                ],
                condition=Q(status="booked"),
                name="uniq_active_appt_slot",
            ),
        ]

    def __str__(self):
        return (
            f"{self.visitor_name} — "
            f"{self.appointment_date} "
            f"{self.start_time.strftime('%H:%M')}"
        )
