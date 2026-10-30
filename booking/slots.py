
from datetime import time

from django.utils import timezone

from calendar_for_admin.models import ScheduleRule, Appointment

from .models import Booking


LIMITS = {
    1: (5, 10),    # деканат
    2: (10, 20),   # заместитель директора
    3: (10, 30),   # директор
}

STEP_MINUTES = 5


def duration_limits(level):
    return LIMITS.get(level, (5, 10))


def to_min(t):
    return t.hour * 60 + t.minute


def free_slot_rules(question, day, duration):
    """
    Возвращает пары (время, правило расписания).
    Учитывает Booking и Appointment.
    """
    today = timezone.localdate()

    if day < today:
        return []

    responsible = question.responsible

    if responsible is None:
        return []

    rules = ScheduleRule.objects.filter(
        administrator=responsible,
        weekday=day.weekday(),
        is_active=True,
    ).order_by("start_time")

    if not rules.exists():
        return []

    busy = []

    bookings = Booking.objects.filter(
        schedule_rule__administrator=responsible,
        date=day,
        status="active",
    )

    for booking in bookings:
        start = to_min(booking.time)
        busy.append((start, start + booking.duration))

    appointments = Appointment.objects.filter(
        administrator=responsible,
        appointment_date=day,
        status="booked",
    )

    for appointment in appointments:
        busy.append((
            to_min(appointment.start_time),
            to_min(appointment.end_time),
        ))

    now_min = (
        to_min(timezone.localtime().time())
        if day == today
        else -1
    )

    result = []

    for rule in rules:
        start = to_min(rule.start_time)
        end = to_min(rule.end_time)

        current = start

        while current + duration <= end:
            is_free = all(
                current + duration <= busy_start
                or current >= busy_end
                for busy_start, busy_end in busy
            )

            if is_free and current > now_min:
                result.append((
                    time(current // 60, current % 60),
                    rule,
                ))

            current += STEP_MINUTES

    return result


def free_slots(question, day, duration):
    """
    Возвращает только время для существующего API.
    """
    return [
        slot_time
        for slot_time, rule in free_slot_rules(
            question,
            day,
            duration,
        )
    ]
