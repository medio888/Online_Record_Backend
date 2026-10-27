
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Booking
from .serializers import BookingTicketSerializer


class MyBookingSerializer(BookingTicketSerializer):
    class Meta(BookingTicketSerializer.Meta):
        fields = [
            "id",
            *BookingTicketSerializer.Meta.fields,
        ]


class MyBookingsView(generics.ListAPIView):
    serializer_class = MyBookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Booking.objects
            .filter(student__user=self.request.user)
            .select_related("student", "question")
            .order_by("-date", "-time")
        )
