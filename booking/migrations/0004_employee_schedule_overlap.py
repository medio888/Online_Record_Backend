
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0003_remove_booking_unique_active_slot_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE booking_booking
                DROP CONSTRAINT IF EXISTS no_overlapping_active_booking;

                ALTER TABLE booking_booking
                ADD CONSTRAINT no_overlapping_active_booking
                EXCLUDE USING gist (
                    schedule_rule_id WITH =,
                    (
                        tsrange(
                            date + "time",
                            date + "time" + duration * INTERVAL '1 minute',
                            '[)'
                        )
                    ) WITH &&
                )
                WHERE (
                    status = 'active'
                    AND schedule_rule_id IS NOT NULL
                );
            """,
            reverse_sql="""
    ALTER TABLE booking_booking
    DROP CONSTRAINT IF EXISTS no_overlapping_active_booking;

    ALTER TABLE booking_booking
    ADD CONSTRAINT no_overlapping_active_booking
    EXCLUDE USING gist (
        level WITH =,
        date WITH =,
        (
            tsrange(
                date + "time",
                date + "time" + duration * INTERVAL '1 minute',
                '[)'
            )
        ) WITH &&
    )
    WHERE (status = 'active');
""",
        ),
    ]
