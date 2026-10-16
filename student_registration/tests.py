
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Student, QueueTicket


User = get_user_model()


class QueueSecurityTests(APITestCase):
    def setUp(self):
        # Создаём двух студентов
        self.user1 = User.objects.create_user(
            username="student_one",
            password="TestPass123!",
        )
        self.user2 = User.objects.create_user(
            username="student_two",
            password="TestPass123!",
        )

        self.student1 = Student.objects.create(
            user=self.user1,
            first_name="Первый",
            last_name="Студент",
            phone="+996700000001",
            direction="it",
            course=1,
        )

        self.student2 = Student.objects.create(
            user=self.user2,
            first_name="Второй",
            last_name="Студент",
            phone="+996700000002",
            direction="it",
            course=1,
        )

        # Администратор для управления очередью
        self.admin = User.objects.create_user(
            username="queue_admin",
            password="AdminPass123!",
            is_staff=True,
        )

        self.queue_url = reverse("queue-join")
        self.call_next_url = reverse("queue-call-next")

    def test_student_cannot_manage_another_students_ticket(self):
        """Студент не может изменить чужой талон."""
        ticket = QueueTicket.objects.create(
            student=self.student2,
            direction="it",
            number=1,
            date=timezone.localdate(),
            status="waiting",
        )

        self.client.force_authenticate(user=self.user1)

        response = self.client.patch(
            reverse("queue-update", kwargs={"pk": ticket.pk}),
            {"status": "cancelled"},
            format="json",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "waiting")

    def test_non_staff_user_cannot_call_next_ticket(self):
        """Обычный пользователь не может вызвать следующего."""
        QueueTicket.objects.create(
            student=self.student1,
            direction="it",
            number=1,
            date=timezone.localdate(),
            status="waiting",
        )

        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            f"{self.call_next_url}?direction=it",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        ticket = QueueTicket.objects.get(number=1, direction="it")
        self.assertEqual(ticket.status, "waiting")

    def test_cancelled_ticket_allows_student_to_join_again(self):
        """После отмены студент может снова встать в очередь."""
        old_ticket = QueueTicket.objects.create(
            student=self.student1,
            direction="it",
            number=1,
            date=timezone.localdate(),
            status="waiting",
        )

        # Администратор отменяет талон
        self.client.force_authenticate(user=self.admin)

        cancel_response = self.client.patch(
            reverse("queue-update", kwargs={"pk": old_ticket.pk}),
            {"status": "cancelled"},
            format="json",
        )

        self.assertEqual(
            cancel_response.status_code,
            status.HTTP_200_OK,
        )

        old_ticket.refresh_from_db()
        self.assertEqual(old_ticket.status, "cancelled")

        # Студент повторно записывается в очередь
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            self.queue_url,
            {"direction": "it"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            QueueTicket.objects.filter(
                student=self.student1,
                date=timezone.localdate(),
                status__in=["waiting", "called"],
            ).count(),
            1,
        )

    def test_anonymous_user_cannot_join_queue(self):
        """Неавторизованный пользователь не может встать в очередь."""
        response = self.client.post(
            self.queue_url,
            {"direction": "it"},
            format="json",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )
        self.assertEqual(QueueTicket.objects.count(), 0)

    def test_anonymous_user_cannot_call_next_ticket(self):
        """Неавторизованный пользователь не может вызвать следующего."""
        ticket = QueueTicket.objects.create(
            student=self.student1,
            direction="it",
            number=1,
            date=timezone.localdate(),
            status="waiting",
        )

        response = self.client.post(
            f"{self.call_next_url}?direction=it",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "waiting")

    def test_anonymous_user_cannot_update_ticket(self):
        """Неавторизованный пользователь не может менять талон."""
        ticket = QueueTicket.objects.create(
            student=self.student1,
            direction="it",
            number=1,
            date=timezone.localdate(),
            status="waiting",
        )

        response = self.client.patch(
            reverse("queue-update", kwargs={"pk": ticket.pk}),
            {"status": "cancelled"},
            format="json",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "waiting")

    def test_anonymous_user_cannot_open_reception_screen(self):
        """Экран приёма доступен только сотрудникам."""
        response = self.client.get(
            f"{reverse('reception-screen')}?direction=it",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )