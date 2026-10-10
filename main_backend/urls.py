from django.urls import path
from .views import StudentRegisterView

urlpatterns = [
    path("register/", StudentRegisterView.as_view(), name="student-register"),
]