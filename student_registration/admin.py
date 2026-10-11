from django import forms
from django.contrib import admin

from .models import Student, QueueTicket


class StudentAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = "__all__"
        widgets = {
            "phone": forms.TextInput(
                attrs={"maxlength": 13, "placeholder": "+996XXXXXXXXX"}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["phone"].initial = "+996"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ("last_name", "first_name", "phone", "direction", "course", "created_at")
    list_filter = ("direction", "course")
    search_fields = ("last_name", "first_name", "phone")


@admin.register(QueueTicket)
class QueueTicketAdmin(admin.ModelAdmin):
    list_display = ("number", "direction", "student", "status", "date")
    list_filter = ("direction", "status", "date")
