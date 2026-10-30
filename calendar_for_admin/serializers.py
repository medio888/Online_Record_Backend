
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework import serializers

from booking.models import Booking
from .models import ScheduleRule, Appointment


User = get_user_model()


def has_booking_conflict(
    administrator_id,
    appointment_date,
    start_time,
    end_time,
):
    """Проверяет пересечение с активными записями студентов."""

    requested_start = datetime.combine(
        appointment_date,
        start_time,
    )
    requested_end = datetime.combine(
        appointment_date,
        end_time,
    )

    bookings = Booking.objects.filter(
        schedule_rule__administrator_id=administrator_id,
        date=appointment_date,
        status="active",
    )

    for booking in bookings:
        booking_start = datetime.combine(
            booking.date,
            booking.time,
        )
        booking_end = booking_start + timedelta(
            minutes=booking.duration
        )

        if (
            booking_start < requested_end
            and booking_end > requested_start
        ):
            return True

    return False


class ScheduleRuleSerializer(serializers.ModelSerializer):
    administrator = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    weekday_name = serializers.CharField(
        source="get_weekday_display",
        read_only=True,
    )

    class Meta:
        model = ScheduleRule
        fields = [
            "id",
            "administrator",
            "weekday",
            "weekday_name",
            "start_time",
            "end_time",
            "slot_duration_minutes",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "administrator",
            "created_at",
        ]

    def validate(self, attrs):
        instance = self.instance

        weekday = attrs.get(
            "weekday",
            instance.weekday if instance else None,
        )

        start_time = attrs.get(
            "start_time",
            instance.start_time if instance else None,
        )

        end_time = attrs.get(
            "end_time",
            instance.end_time if instance else None,
        )

        duration = attrs.get(
            "slot_duration_minutes",
            instance.slot_duration_minutes if instance else 30,
        )

        is_active = attrs.get(
            "is_active",
            instance.is_active if instance else True,
        )

        if weekday is None or weekday not in range(7):
            raise serializers.ValidationError({
                "weekday": "Выберите день недели от 0 до 6."
            })

        if start_time is None or end_time is None:
            raise serializers.ValidationError(
                "Укажите время начала и окончания приёма."
            )

        if start_time >= end_time:
            raise serializers.ValidationError({
                "end_time": (
                    "Время окончания должно быть позже времени начала."
                )
            })

        if duration < 5 or duration > 240:
            raise serializers.ValidationError({
                "slot_duration_minutes": (
                    "Длительность сеанса должна быть от 5 до 240 минут."
                )
            })

        start = datetime.combine(
            timezone.localdate(),
            start_time,
        )

        end = datetime.combine(
            timezone.localdate(),
            end_time,
        )

        if start + timedelta(minutes=duration) > end:
            raise serializers.ValidationError({
                "slot_duration_minutes": (
                    "Время приёма должно вмещать хотя бы один полный сеанс."
                )
            })

        request = self.context.get("request")

        if instance:
            administrator = instance.administrator
        elif request:
            administrator = request.user
        else:
            administrator = None

        if is_active and administrator:
            overlapping_rules = ScheduleRule.objects.filter(
                administrator=administrator,
                weekday=weekday,
                is_active=True,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            if instance:
                overlapping_rules = overlapping_rules.exclude(
                    pk=instance.pk
                )

            if overlapping_rules.exists():
                raise serializers.ValidationError({
                    "start_time": (
                        "Новое расписание пересекается "
                        "с другим активным расписанием."
                    )
                })

        if instance:
            has_appointments = instance.appointments.filter(
                status="booked"
            ).exists()

            has_bookings = Booking.objects.filter(
                schedule_rule=instance,
                status="active",
            ).exists()

            if has_appointments or has_bookings:
                changed = (
                    weekday != instance.weekday
                    or start_time != instance.start_time
                    or end_time != instance.end_time
                    or duration != instance.slot_duration_minutes
                )

                if changed:
                    raise serializers.ValidationError({
                        "detail": (
                            "Нельзя изменять время расписания, "
                            "пока существуют активные записи. "
                            "Сначала отмените записи или создайте "
                            "новое правило."
                        )
                    })

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Для создания расписания необходимо войти в систему."
            )

        validated_data["administrator"] = request.user

        return super().create(validated_data)


class AppointmentSerializer(serializers.ModelSerializer):
    administrator = serializers.IntegerField(
        source="administrator_id",
        read_only=True,
    )

    class Meta:
        model = Appointment
        fields = [
            "id",
            "schedule_rule",
            "administrator",
            "appointment_date",
            "start_time",
            "end_time",
            "visitor_name",
            "visitor_phone",
            "status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "administrator",
            "end_time",
            "status",
            "created_at",
        ]

    def validate_visitor_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Укажите имя посетителя."
            )

        return value

    def validate_visitor_phone(self, value):
        value = value.strip()

        if len(value) < 5:
            raise serializers.ValidationError(
                "Укажите корректный номер телефона."
            )

        return value

    def create(self, validated_data):
        rule = validated_data["schedule_rule"]
        appointment_date = validated_data["appointment_date"]
        start_time = validated_data["start_time"]
        end_time = validated_data["end_time"]

        try:
            with transaction.atomic():
                administrator = (
                    User.objects.select_for_update()
                    .get(pk=rule.administrator_id)
                )

                rule.refresh_from_db()

                if not rule.is_active:
                    raise serializers.ValidationError({
                        "schedule_rule": "Это расписание неактивно."
                    })

                conflicts = Appointment.objects.filter(
                    administrator_id=administrator.pk,
                    appointment_date=appointment_date,
                    status="booked",
                    start_time__lt=end_time,
                    end_time__gt=start_time,
                )

                if conflicts.exists():
                    raise serializers.ValidationError({
                        "start_time": (
                            "Это время уже занято. Выберите другой сеанс."
                        )
                    })

                if has_booking_conflict(
                    administrator.pk,
                    appointment_date,
                    start_time,
                    end_time,
                ):
                    raise serializers.ValidationError({
                        "start_time": (
                            "Это время уже занято записью студента."
                        )
                    })

                validated_data["administrator"] = administrator

                return super().create(validated_data)

        except IntegrityError:
            raise serializers.ValidationError({
                "start_time": (
                    "Это время только что заняли. "
                    "Обновите список доступных сеансов."
                )
            })

    def validate(self, attrs):
        rule = attrs["schedule_rule"]
        appointment_date = attrs["appointment_date"]
        start_time = attrs["start_time"]

        today = timezone.localdate()
        last_date = today + timedelta(days=29)

        if not rule.is_active:
            raise serializers.ValidationError({
                "schedule_rule": "Это расписание неактивно."
            })

        if not today <= appointment_date <= last_date:
            raise serializers.ValidationError({
                "appointment_date": (
                    "Можно записаться только на ближайшие "
                    "30 календарных дней, включая сегодня."
                )
            })

        if appointment_date.weekday() != rule.weekday:
            raise serializers.ValidationError({
                "appointment_date": (
                    "Выбранная дата не соответствует "
                    "дню недели расписания."
                )
            })

        duration = timedelta(
            minutes=rule.slot_duration_minutes
        )

        current = datetime.combine(
            appointment_date,
            rule.start_time,
        )

        finish = datetime.combine(
            appointment_date,
            rule.end_time,
        )

        requested_start = datetime.combine(
            appointment_date,
            start_time,
        )

        valid_starts = []

        while current + duration <= finish:
            valid_starts.append(current.time())
            current += duration

        if start_time not in valid_starts:
            raise serializers.ValidationError({
                "start_time": (
                    "Выбранное время не входит в доступные сеансы."
                )
            })

        requested_end = requested_start + duration

        if appointment_date == today:
            current_time = timezone.localtime().time().replace(
                tzinfo=None
            )

            if start_time <= current_time:
                raise serializers.ValidationError({
                    "start_time": "Выбранное время уже прошло."
                })

        conflicts = Appointment.objects.filter(
            schedule_rule__administrator=rule.administrator,
            appointment_date=appointment_date,
            status="booked",
            start_time__lt=requested_end.time(),
            end_time__gt=start_time,
        )

        if self.instance:
            conflicts = conflicts.exclude(
                pk=self.instance.pk
            )

        if conflicts.exists():
            raise serializers.ValidationError({
                "start_time": (
                    "Это время уже занято или пересекается "
                    "с другой записью администратора."
                )
            })

        if has_booking_conflict(
            rule.administrator_id,
            appointment_date,
            start_time,
            requested_end.time(),
        ):
            raise serializers.ValidationError({
                "start_time": (
                    "Это время уже занято записью студента."
                )
            })

        attrs["end_time"] = requested_end.time()

        return attrs
