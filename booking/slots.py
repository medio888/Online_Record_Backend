"""
Расписание общей записи по вопросам студентов.

Используется модулем booking.
Рабочие дни и часы задаются фиксированными правилами.
Индивидуальные графики сотрудников обслуживаются
отдельным приложением calendar_for_admin.
"""


from datetime import time

from django.utils import timezone

from .models import Booking

WORK_DAYS = {0, 1, 2, 3, 4}   # пн-пт
START = time(10, 0)
END = time(17, 0)
STEP_MINUTES = 5

# уровень вопроса: (минимум, максимум) минут
LIMITS = {
    1: (5, 10),    # деканат
    2: (10, 20),   # заместитель директора
    3: (10, 30),   # директор
}


def duration_limits(level):
    return LIMITS.get(level, (5, 10))


def to_min(t):
    return t.hour * 60 + t.minute


def free_slots(level, day, duration):
    today = timezone.localdate()
    if day < today or day.weekday() not in WORK_DAYS:
        return []

    busy = [
        (to_min(b.time), to_min(b.time) + b.duration)
        for b in Booking.objects.filter(level=level, date=day, status="active")
    ]
    now_min = to_min(timezone.localtime().time()) if day == today else -1

    result = []
    m = to_min(START)
    end = to_min(END)
    while m + duration <= end:
        free = all(m + duration <= bs or m >= be for bs, be in busy)
        if free and m > now_min:
            result.append(time(m // 60, m % 60))
        m += STEP_MINUTES
    return result
