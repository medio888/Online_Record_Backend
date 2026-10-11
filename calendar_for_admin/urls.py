
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AvailabilityView,
    ScheduleRuleViewSet,
    AppointmentViewSet,
    AppointmentBookingView,
)

router = DefaultRouter()
router.register(
    "rules",
    ScheduleRuleViewSet,
    basename="schedule-rule",
)
router.register(
    "appointments",
    AppointmentViewSet,
    basename="appointment",
)

urlpatterns = [
    path("availability/", AvailabilityView.as_view(), name="availability"),
    path("book/", AppointmentBookingView.as_view(), name="appointment-book"),
    path("", include(router.urls)),
]
