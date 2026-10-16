
from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from .models import ScheduleRule, Appointment
from django.db import IntegrityError, transaction
from django.test import TransactionTestCase

User = get_user_model()


class CalendarAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="calendar_admin",
            password="Test-Password-123!",
            is_staff=True,
        )

        self.visitor = User.objects.create_user(
            username="calendar_visitor",
            password="Test-Password-456!",
        )

        date = timezone.localdate() + timedelta(days=1)

        while date.weekday() != 0:
            date += timedelta(days=1)

        self.appointment_date = date

        self.rule = ScheduleRule.objects.create(
            administrator=self.admin,
            weekday=date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            slot_duration_minutes=30,
            is_active=True,
        )

    def test_public_user_cannot_create_schedule_rule(self):
        response = self.client.post(
            reverse("schedule-rule-list"),
            {
                "weekday": 1,
                "start_time": "09:00",
                "end_time": "10:00",
                "slot_duration_minutes": 30,
                "is_active": True,
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

    def test_available_slots_are_public(self):
        response = self.client.get(
            reverse("availability")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("available_dates", response.data)

    def test_same_slot_cannot_be_booked_twice(self):
        payload = {
            "schedule_rule": self.rule.id,
            "appointment_date": self.appointment_date.isoformat(),
            "start_time": "09:00",
            "visitor_name": "Тестовый посетитель",
            "visitor_phone": "+996555123456",
        }

        first_response = self.client.post(
            reverse("appointment-book"),
            payload,
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = self.client.post(
            reverse("appointment-book"),
            payload,
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Appointment.objects.filter(
                schedule_rule=self.rule,
                appointment_date=self.appointment_date,
                start_time=time(9, 0),
                status="booked",
            ).count(),
            1,
        )


class CalendarOverlapConstraintTests(TransactionTestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="overlap_calendar_admin",
            password="Test-Password-123!",
            is_staff=True,
        )
        self.visitor1 = "Первый посетитель"
        self.visitor2 = "Второй посетитель"

        self.appointment_date = timezone.localdate() + timedelta(days=1)
        while self.appointment_date.weekday() >= 5:
            self.appointment_date += timedelta(days=1)

        self.rule = ScheduleRule.objects.create(
            administrator=self.admin,
            weekday=self.appointment_date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            slot_duration_minutes=30,
            is_active=True,
        )

    def test_overlapping_appointments_are_rejected_by_database(self):
        Appointment.objects.create(
            schedule_rule=self.rule,
            administrator=self.admin,
            appointment_date=self.appointment_date,
            start_time=time(9, 0),
            end_time=time(9, 30),
            visitor_name=self.visitor1,
            visitor_phone="+996555123451",
            status="booked",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Appointment.objects.create(
                    schedule_rule=self.rule,
                    administrator=self.admin,
                    appointment_date=self.appointment_date,
                    start_time=time(9, 15),
                    end_time=time(9, 45),
                    visitor_name=self.visitor2,
                    visitor_phone="+996555123452",
                    status="booked",
                )

    def test_adjacent_appointments_are_allowed(self):
        Appointment.objects.create(
            schedule_rule=self.rule,
            administrator=self.admin,
            appointment_date=self.appointment_date,
            start_time=time(9, 0),
            end_time=time(9, 30),
            visitor_name=self.visitor1,
            visitor_phone="+996555123451",
            status="booked",
        )

        second = Appointment.objects.create(
            schedule_rule=self.rule,
            administrator=self.admin,
            appointment_date=self.appointment_date,
            start_time=time(9, 30),
            end_time=time(10, 0),
            visitor_name=self.visitor2,
            visitor_phone="+996555123452",
            status="booked",
        )

        self.assertEqual(second.start_time, time(9, 30))


def _results(response):
    """Список из ответа: работает и с пагинацией, и без неё."""
    data = response.data
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data


class CalendarStaffIsolationTests(APITestCase):
    """Сотрудник управляет только своим расписанием и своими записями."""

    def setUp(self):
        self.admin1 = User.objects.create_user(
            username="isolation_admin_1",
            password="Test-Password-123!",
            is_staff=True,
        )
        self.admin2 = User.objects.create_user(
            username="isolation_admin_2",
            password="Test-Password-456!",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="isolation_regular_user",
            password="Test-Password-789!",
        )

        self.appointment_date = timezone.localdate() + timedelta(days=1)

        self.rule1 = ScheduleRule.objects.create(
            administrator=self.admin1,
            weekday=self.appointment_date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            slot_duration_minutes=30,
            is_active=True,
        )

        self.appointment1 = Appointment.objects.create(
            schedule_rule=self.rule1,
            administrator=self.admin1,
            appointment_date=self.appointment_date,
            start_time=time(9, 0),
            end_time=time(9, 30),
            visitor_name="Первый посетитель",
            visitor_phone="+996555123456",
            status="booked",
        )

    def test_staff_cannot_update_another_admins_rule(self):
        self.client.force_authenticate(user=self.admin2)

        response = self.client.patch(
            reverse("schedule-rule-detail", kwargs={"pk": self.rule1.pk}),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.rule1.refresh_from_db()
        self.assertTrue(self.rule1.is_active)

    def test_staff_cannot_delete_another_admins_rule(self):
        self.client.force_authenticate(user=self.admin2)

        response = self.client.delete(
            reverse("schedule-rule-detail", kwargs={"pk": self.rule1.pk}),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertTrue(
            ScheduleRule.objects.filter(pk=self.rule1.pk).exists()
        )

    def test_staff_does_not_see_another_admins_rules_and_appointments(self):
        self.client.force_authenticate(user=self.admin2)

        rules_response = self.client.get(
            reverse("schedule-rule-list")
        )
        appointments_response = self.client.get(
            reverse("appointment-list")
        )

        self.assertEqual(
            rules_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            appointments_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(_results(rules_response), [])
        self.assertEqual(_results(appointments_response), [])

    def test_staff_cannot_cancel_another_admins_appointment(self):
        self.client.force_authenticate(user=self.admin2)

        response = self.client.post(
            reverse(
                "appointment-cancel",
                kwargs={"pk": self.appointment1.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.appointment1.refresh_from_db()
        self.assertEqual(self.appointment1.status, "booked")

    def test_non_staff_user_cannot_manage_schedule(self):
        self.client.force_authenticate(user=self.regular_user)

        rules_response = self.client.get(
            reverse("schedule-rule-list")
        )
        cancel_response = self.client.post(
            reverse(
                "appointment-cancel",
                kwargs={"pk": self.appointment1.pk},
            )
        )

        self.assertEqual(
            rules_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            cancel_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.appointment1.refresh_from_db()
        self.assertEqual(self.appointment1.status, "booked")

    def _available_starts(self):
        response = self.client.get(reverse("availability"))

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        for day in response.data["available_dates"]:
            if day["date"] == self.appointment_date.isoformat():
                return {slot["start_time"] for slot in day["slots"]}

        return set()

    def test_cancelled_appointment_frees_its_slot(self):
        # Пока запись активна, занятое время не предлагается.
        starts = self._available_starts()
        self.assertNotIn("09:00", starts)
        self.assertIn("09:30", starts)

        # Владелец расписания отменяет запись.
        self.client.force_authenticate(user=self.admin1)

        cancel_response = self.client.post(
            reverse(
                "appointment-cancel",
                kwargs={"pk": self.appointment1.pk},
            )
        )

        self.assertEqual(
            cancel_response.status_code,
            status.HTTP_200_OK,
        )

        self.appointment1.refresh_from_db()
        self.assertEqual(self.appointment1.status, "cancelled")

        # После отмены время снова доступно.
        self.client.force_authenticate(user=None)
        starts = self._available_starts()
        self.assertIn("09:00", starts)
        self.assertIn("09:30", starts)

    def test_appointments_list_is_paginated(self):
        # 25 непересекающихся записей по 10 минут у admin1.
        for i in range(1, 26):
            start_minutes = 10 * 60 + i * 10
            end_minutes = start_minutes + 10

            Appointment.objects.create(
                schedule_rule=self.rule1,
                administrator=self.admin1,
                appointment_date=self.appointment_date,
                start_time=time(start_minutes // 60, start_minutes % 60),
                end_time=time(end_minutes // 60, end_minutes % 60),
                visitor_name=f"Посетитель {i}",
                visitor_phone="+996555123456",
                status="booked",
            )

        self.client.force_authenticate(user=self.admin1)

        response = self.client.get(reverse("appointment-list"))

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        # 25 новых записей + appointment1 из setUp.
        self.assertEqual(response.data["count"], 26)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIsNotNone(response.data["next"])

        small_page = self.client.get(
            reverse("appointment-list"),
            {"page_size": 5},
        )

        self.assertEqual(len(small_page.data["results"]), 5)