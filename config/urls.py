from django.contrib import admin
from django.urls import path, include

from rest_framework.decorators import api_view
from rest_framework.response import Response

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


@api_view(["GET"])
def api_root(request, format=None):
    return Response({
        "register": "/api/register/",
        "queue": "/api/queue/",
        "queue_join": "/api/queue/join/",
        "queue_call_next": "/api/queue/call-next/",
        "questions": "/api/questions/",
        "categories": "/api/questions/categories/",
        "levels": "/api/questions/levels/",
        "appeals": "/api/questions/appeals/",
        "booking": "/api/booking/",
        "booking_route": "/api/booking/route/",
        "booking_slots": "/api/booking/slots/",
        "calendar_availability": "/api/calendar/availability/",
        "calendar_book": "/api/calendar/book/",
        "calendar_rules": "/api/calendar/rules/",
        "calendar_appointments": "/api/calendar/appointments/",
        "schema": "/api/schema/",
        "swagger": "/api/docs/",
        "admin": "/admin/",
    })


urlpatterns = [
    path("admin/", admin.site.urls),

    # API Root
    path("", api_root, name="api-root"),

    # Регистрация и очередь
    path("api/", include("student_registration.urls")),

    # Вопросы и обращения
    path("api/questions/", include("questions.urls")),

    # Запись на приём к администрации
    path("api/calendar/", include("calendar_for_admin.urls")),

    # Бронирование времени
    path("api/booking/", include("booking.urls")),

    # Swagger и OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
