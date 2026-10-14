from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from questions.models import Question, QuestionCategory
from student_registration.models import Student
from .models import Booking
from .slots import free_slots

from django.db import IntegrityError, transaction
from django.test import TransactionTestCase

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

User = get_user_model()


class BookingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="booking_student",
            password="Test-Password-123!",
        )

        cls.student = Student.objects.create(
            user=cls.user,
            first_name="РўРµСЃС‚",
            last_name="РЎС‚СѓРґРµРЅС‚",
            phone="+996555123456",
            direction="it",
            course=1,
        )

        cls.category = QuestionCategory.objects.create(
            title="РўРµСЃС‚РѕРІР°СЏ РєР°С‚РµРіРѕСЂРёСЏ",
        )

        cls.question = Question.objects.create(
            category=cls.category,
            text="РўРµСЃС‚РѕРІС‹Р№ РІРѕРїСЂРѕСЃ",
            level=Question.Level.DEAN,
            is_active=True,
        )

    def setUp(self):
        day = timezone.localdate() + timedelta(days=1)

        while day.weekday() >= 5:
            day += timedelta(days=1)

        self.booking_date = day

    def test_booking_can_be_created(self):
        booking = Booking.objects.create(
            student=self.student,
            question=self.question,
            level=self.question.level,
            date=self.booking_date,
            time=time(10, 0),
            duration=10,
        )

        self.assertEqual(booking.status, "active")
        self.assertEqual(
            Booking.objects.filter(pk=booking.pk).count(),
            1,
        )

    def test_free_slots_excludes_overlapping_booking(self):
        Booking.objects.create(
            student=self.student,
            question=self.question,
            level=self.question.level,
            date=self.booking_date,
            time=time(10, 0),
            duration=10,
        )

        slots = free_slots(
            self.question.level,
            self.booking_date,
            10,
        )

        self.assertNotIn(time(10, 0), slots)
        self.assertNotIn(time(10, 5), slots)
        self.assertIn(time(10, 10), slots)

    def test_cancelled_booking_does_not_block_slot(self):
        Booking.objects.create(
            student=self.student,
            question=self.question,
            level=self.question.level,
            date=self.booking_date,
            time=time(10, 0),
            duration=10,
            status="cancelled",
        )

        slots = free_slots(
            self.question.level,
            self.booking_date,
            10,
        )

        self.assertIn(time(10, 0), slots)



class BookingOverlapConstraintTests(TransactionTestCase):
    reset_sequences = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="overlap_student_1",
            password="Test-Password-123!",
        )
        self.user2 = User.objects.create_user(
            username="overlap_student_2",
            password="Test-Password-456!",
        )

        self.student1 = Student.objects.create(
            user=self.user1,
            first_name="РџРµСЂРІС‹Р№",
            last_name="РЎС‚СѓРґРµРЅС‚",
            phone="+996555123457",
            direction="it",
            course=1,
        )
        self.student2 = Student.objects.create(
            user=self.user2,
            first_name="Р’С‚РѕСЂРѕР№",
            last_name="РЎС‚СѓРґРµРЅС‚",
            phone="+996555123458",
            direction="it",
            course=1,
        )

        self.category = QuestionCategory.objects.create(
            title="РџСЂРѕРІРµСЂРєР° РїРµСЂРµСЃРµС‡РµРЅРёР№",
        )
        self.question = Question.objects.create(
            category=self.category,
            text="РџСЂРѕРІРµСЂРєР° РёРЅС‚РµСЂРІР°Р»РѕРІ",
            level=Question.Level.DEAN,
            is_active=True,
        )

        self.booking_date = timezone.localdate() + timedelta(days=1)
        while self.booking_date.weekday() >= 5:
            self.booking_date += timedelta(days=1)

    def test_overlapping_active_bookings_are_rejected_by_database(self):
        Booking.objects.create(
            student=self.student1,
            question=self.question,
            level=self.question.level,
            date=self.booking_date,
            time=time(10, 0),
            duration=20,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Booking.objects.create(
                    student=self.student2,
                    question=self.question,
                    level=self.question.level,
                    date=self.booking_date,
                    time=time(10, 15),
                    duration=10,
                )

    def test_adjacent_bookings_are_allowed(self):
        Booking.objects.create(
            student=self.student1,
            question=self.question,
            level=self.question.level,
            date=self.booking_date,
            time=time(10, 0),
            duration=10,
        )

        second = Booking.objects.create(
            student=self.student2,
            question=self.question,
            level=self.question.level,
            date=self.booking_date,
            time=time(10, 10),
            duration=10,
        )

        self.assertEqual(second.time, time(10, 10))


class ParallelBookingAPITests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="parallel_student_1",
            password="Test-Password-123!",
        )
        self.user2 = User.objects.create_user(
            username="parallel_student_2",
            password="Test-Password-456!",
        )

        self.student1 = Student.objects.create(
            user=self.user1,
            first_name="РџРµСЂРІС‹Р№",
            last_name="РЎС‚СѓРґРµРЅС‚",
            phone="+996555123457",
            direction="it",
            course=1,
        )
        self.student2 = Student.objects.create(
            user=self.user2,
            first_name="Р’С‚РѕСЂРѕР№",
            last_name="РЎС‚СѓРґРµРЅС‚",
            phone="+996555123458",
            direction="it",
            course=1,
        )

        self.category = QuestionCategory.objects.create(
            title="РџР°СЂР°Р»Р»РµР»СЊРЅРѕРµ Р±СЂРѕРЅРёСЂРѕРІР°РЅРёРµ",
        )
        self.question = Question.objects.create(
            category=self.category,
            text="РџСЂРѕРІРµСЂРєР° РїРµСЂРµСЃРµРєР°СЋС‰РёС…СЃСЏ Р·Р°РїРёСЃРµР№",
            level=Question.Level.DEAN,
            is_active=True,
        )

        self.booking_date = timezone.localdate() + timedelta(days=1)
        while self.booking_date.weekday() >= 5:
            self.booking_date += timedelta(days=1)

    def test_parallel_overlapping_requests_create_only_one_booking(self):
        barrier = Barrier(2)

        def send_booking(user, start_time):
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(user=user)

                payload = {
                    "question": self.question.pk,
                    "date": self.booking_date.isoformat(),
                    "time": start_time,
                    "duration": 10,
                }

                # РћР±Р° РїРѕС‚РѕРєР° РЅР°С‡РёРЅР°СЋС‚ РѕС‚РїСЂР°РІРєСѓ РІРјРµСЃС‚Рµ.
                barrier.wait(timeout=10)

                response = client.post(
                    reverse("booking-create"),
                    payload,
                    format="json",
                )

                return response.status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(
                send_booking, self.user1, "10:00"
            )
            future2 = executor.submit(
                send_booking, self.user2, "10:05"
            )

            results = [
                future1.result(timeout=30),
                future2.result(timeout=30),
            ]

        self.assertEqual(
            results.count(status.HTTP_201_CREATED),
            1,
            msg=f"РћР¶РёРґР°Р»СЃСЏ СЂРѕРІРЅРѕ РѕРґРёРЅ СѓСЃРїРµС€РЅС‹Р№ Р·Р°РїСЂРѕСЃ: {results}",
        )
        self.assertEqual(
            results.count(status.HTTP_400_BAD_REQUEST),
            1,
            msg=f"Р’С‚РѕСЂРѕР№ Р·Р°РїСЂРѕСЃ РґРѕР»Р¶РµРЅ РїРѕР»СѓС‡РёС‚СЊ РѕС‚РєР°Р·: {results}",
        )

        self.assertEqual(
            Booking.objects.filter(status="active").count(),
            1,
        )

