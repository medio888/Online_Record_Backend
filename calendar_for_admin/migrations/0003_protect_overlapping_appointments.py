
from django.db import migrations


def fill_administrators(apps, schema_editor):
    Appointment = apps.get_model(
        "calendar_for_admin",
        "Appointment",
    )

    appointments = Appointment.objects.filter(
        administrator__isnull=True,
    ).select_related("schedule_rule")

    for appointment in appointments.iterator():
        appointment.administrator_id = (
            appointment.schedule_rule.administrator_id
        )
        appointment.save(update_fields=["administrator"])


def clear_administrators(apps, schema_editor):
    Appointment = apps.get_model(
        "calendar_for_admin",
        "Appointment",
    )
    Appointment.objects.update(administrator=None)


class Migration(migrations.Migration):

    dependencies = [
        ("calendar_for_admin", "0002_appointment_administrator"),
    ]

    operations = [
        migrations.RunPython(
            fill_administrators,
            clear_administrators,
        ),
        migrations.RunSQL(
            sql="""
                CREATE EXTENSION IF NOT EXISTS btree_gist;
                
                ALTER TABLE calendar_for_admin_appointment
                ADD CONSTRAINT no_overlapping_admin_appointment
                EXCLUDE USING gist (
                    administrator_id WITH =,
                    appointment_date WITH =,
                    (
                        tsrange(
                            appointment_date + start_time,
                            appointment_date + end_time,
                            '[)'
                        )
                    ) WITH &&
                )
                WHERE (status = 'booked');
            """,
            reverse_sql="""
                ALTER TABLE calendar_for_admin_appointment
                DROP CONSTRAINT IF EXISTS
                    no_overlapping_admin_appointment;
            """,
        ),
    ]
