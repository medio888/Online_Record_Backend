from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("code", "student", "get_level_display", "date", "time", "duration", "status")
    list_filter = ("level", "status", "date")
    search_fields = ("code", "student__last_name", "student__phone")
