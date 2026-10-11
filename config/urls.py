from django.contrib import admin
from django.urls import path, include

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def api_root(request, format=None):
    return Response({
        "register": "/api/register/",
        "queue": "/api/queue/",
        "questions": "/api/questions/",
        "categories": "/api/questions/categories/",
        "levels": "/api/questions/levels/",
        "appeals": "/api/questions/appeals/",
        "calendar": "/api/calendar/",
        "calendar_availability": "/api/calendar/availability/",
        "calendar_book": "/api/calendar/book/",
        "calendar_rules": "/api/calendar/rules/",
        "calendar_appointments": "/api/calendar/appointments/",
        "swagger": "/api/docs/",
        "admin": "/admin/",
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", api_root, name="api-root"),
    path("api/", include("main_backend.urls")),
    path("api/questions/", include("questions.urls")),
    path("api/calendar/", include("calendar_for_admin.urls")),
]