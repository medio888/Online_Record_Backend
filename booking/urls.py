from django.urls import path

from .views import BookingCreateView, BookingCancelView, RouteView, SlotsView, TicketView

urlpatterns = [
    path("route/", RouteView.as_view(), name="booking-route"),
    path("slots/", SlotsView.as_view(), name="booking-slots"),
    path("ticket/<str:code>/", TicketView.as_view(), name="booking-ticket"),
    path("", BookingCreateView.as_view(), name="booking-create"),
    path("<int:pk>/cancel/", BookingCancelView.as_view(), name="booking-cancel"),
]
