
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .models import QuestionCategory, Question, Appeal


User = get_user_model()


class AppealAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student1 = User.objects.create_user(
            username="appeal_student_1",
            password="Test-Password-123!",
        )
        cls.student2 = User.objects.create_user(
            username="appeal_student_2",
            password="Test-Password-456!",
        )
        cls.staff = User.objects.create_user(
            username="appeal_staff",
            password="Test-Password-789!",
            is_staff=True,
        )

        cls.category = QuestionCategory.objects.create(
            title="Тестовая категория обращений",
        )
        cls.question = Question.objects.create(
            category=cls.category,
            text="Тестовый вопрос",
            level=Question.Level.DEAN,
            is_active=True,
        )

        cls.appeal1 = Appeal.objects.create(
            user=cls.student1,
            question=cls.question,
            message="Первое тестовое обращение",
        )
        cls.appeal2 = Appeal.objects.create(
            user=cls.student2,
            question=cls.question,
            message="Второе тестовое обращение",
        )

    def test_anonymous_user_cannot_list_appeals(self):
        response = self.client.get(
            reverse("appeal-list-create")
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

    def test_anonymous_user_cannot_create_appeal(self):
        response = self.client.post(
            reverse("appeal-list-create"),
            {
                "question": self.question.pk,
                "message": "Анонимное обращение",
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

        self.assertFalse(
            Appeal.objects.filter(
                message="Анонимное обращение"
            ).exists()
        )

    def test_student_sees_only_own_appeals(self):
        self.client.force_authenticate(user=self.student1)

        response = self.client.get(
            reverse("appeal-list-create")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.data
        if isinstance(data, dict) and "results" in data:
            data = data["results"]

        appeal_ids = {item["id"] for item in data}

        self.assertIn(self.appeal1.pk, appeal_ids)
        self.assertNotIn(self.appeal2.pk, appeal_ids)

    def test_staff_can_see_all_appeals(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.get(
            reverse("appeal-list-create")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.data
        if isinstance(data, dict) and "results" in data:
            data = data["results"]

        appeal_ids = {item["id"] for item in data}

        self.assertIn(self.appeal1.pk, appeal_ids)
        self.assertIn(self.appeal2.pk, appeal_ids)

    def test_student_cannot_retrieve_another_users_appeal(self):
        self.client.force_authenticate(user=self.student1)

        response = self.client.get(
            reverse(
                "appeal-detail",
                kwargs={"pk": self.appeal2.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_student_can_retrieve_own_appeal(self):
        self.client.force_authenticate(user=self.student1)

        response = self.client.get(
            reverse(
                "appeal-detail",
                kwargs={"pk": self.appeal1.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_staff_can_retrieve_another_users_appeal(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.get(
            reverse(
                "appeal-detail",
                kwargs={"pk": self.appeal2.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_created_appeal_belongs_to_authenticated_user(self):
        self.client.force_authenticate(user=self.student1)

        response = self.client.post(
            reverse("appeal-list-create"),
            {
                "question": self.question.pk,
                "message": "Моё новое обращение",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=str(response.data),
        )

        appeal = Appeal.objects.get(
            message="Моё новое обращение"
        )

        self.assertEqual(appeal.user, self.student1)
        self.assertEqual(appeal.question, self.question)
        self.assertEqual(appeal.status, Appeal.Status.PENDING)

    def test_creating_appeal_with_nonexistent_question_fails(self):
        self.client.force_authenticate(user=self.student1)

        response = self.client.post(
            reverse("appeal-list-create"),
            {
                "question": 999999,
                "message": "Обращение с неверным вопросом",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )  
    
    def test_staff_can_start_processing_appeal(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(
            reverse(
                "appeal-status-update",
                kwargs={"pk": self.appeal1.pk},
            ),
            {"status": Appeal.Status.IN_PROGRESS},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=str(response.data),
        )

        self.appeal1.refresh_from_db()
        self.assertEqual(
            self.appeal1.status,
            Appeal.Status.IN_PROGRESS,
        )

    def test_student_cannot_change_appeal_status(self):
        self.client.force_authenticate(user=self.student1)

        response = self.client.patch(
            reverse(
                "appeal-status-update",
                kwargs={"pk": self.appeal1.pk},
            ),
            {"status": Appeal.Status.IN_PROGRESS},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.appeal1.refresh_from_db()
        self.assertEqual(
            self.appeal1.status,
            Appeal.Status.PENDING,
        )

    def test_staff_cannot_set_unknown_status(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(
            reverse(
                "appeal-status-update",
                kwargs={"pk": self.appeal1.pk},
            ),
            {"status": "unknown"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.appeal1.refresh_from_db()
        self.assertEqual(
            self.appeal1.status,
            Appeal.Status.PENDING,
        )

    def test_staff_cannot_skip_processing_stage(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(
            reverse(
                "appeal-status-update",
                kwargs={"pk": self.appeal1.pk},
            ),
            {"status": Appeal.Status.RESOLVED},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.appeal1.refresh_from_db()
        self.assertEqual(
            self.appeal1.status,
            Appeal.Status.PENDING,
        )

    def test_resolved_appeal_cannot_change_status_again(self):
        self.appeal1.status = Appeal.Status.RESOLVED
        self.appeal1.save(update_fields=["status"])

        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(
            reverse(
                "appeal-status-update",
                kwargs={"pk": self.appeal1.pk},
            ),
            {"status": Appeal.Status.REJECTED},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.appeal1.refresh_from_db()
        self.assertEqual(
            self.appeal1.status,
            Appeal.Status.RESOLVED,
        )
