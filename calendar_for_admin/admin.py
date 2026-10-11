
from django.contrib import admin

from .models import ScheduleRule, Appointment


@admin.register(ScheduleRule)
class ScheduleRuleAdmin(admin.ModelAdmin):
    list_display = (
        "administrator",
        "weekday",
        "start_time",
        "end_time",
        "slot_duration_minutes",
        "is_active",
    )
    list_filter = ("weekday", "is_active")
    search_fields = ("administrator__username",)
    ordering = ("weekday", "start_time")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "visitor_name",
        "visitor_phone",
        "appointment_date",
        "start_time",
        "end_time",
        "status",
    )
    list_filter = ("status", "appointment_date")
    search_fields = (
        "visitor_name",
        "visitor_phone",
        "schedule_rule__administrator__username",
    )
    readonly_fields = ("created_at",)
    ordering = ("appointment_date", "start_time")
