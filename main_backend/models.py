from django.db import models


class Student(models.Model):
    DIRECTIONS = [
        ("it", "IT"),
        ("business_analytics", "Бизнес-аналитика"),
        ("translator_english", "Переводчики английского"),
        ("translator_korean", "Переводчики корейского"),
        ("law", "Юристы"),
        ("marketing", "Маркетологи"),
        ("design", "Дизайнеры"),
    ]

    COURSES = [
        (1, "1 курс"),
        (2, "2 курс"),
        (3, "3 курс"),
    ]

    first_name = models.CharField("Имя", max_length=50)
    last_name = models.CharField("Фамилия", max_length=50)
    phone = models.CharField("Телефон", max_length=20)
    direction = models.CharField("Направление", max_length=30, choices=DIRECTIONS)
    course = models.PositiveSmallIntegerField("Курс", choices=COURSES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"