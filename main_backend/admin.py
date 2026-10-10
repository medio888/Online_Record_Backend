from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "phone", "direction", "course", "created_at")
    list_filter = ("direction", "course")
    search_fields = ("last_name", "first_name", "phone")
