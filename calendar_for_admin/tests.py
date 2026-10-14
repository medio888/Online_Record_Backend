
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
