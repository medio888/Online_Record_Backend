from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def api_root(request, format=None):
    return Response({
        "questions": "/api/questions/",
        "categories": "/api/questions/categories/",
        "levels": "/api/questions/levels/",
        "appeals": "/api/questions/appeals/",
        "register": "/api/register/",
        "queue": "/api/queue/",
        "swagger": "/api/docs/",
        "admin": "/admin/",
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", api_root, name="api-root"),
    path("api/", include("student_registration.urls")),
    path("api/questions/", include("questions.urls")),
    path("api/", include("questions.urls")),
]