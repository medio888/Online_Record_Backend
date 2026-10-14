from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE EXTENSION IF NOT EXISTS btree_gist;
            
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
            reverse_sql="""
                ALTER TABLE booking_booking
                DROP CONSTRAINT IF EXISTS no_overlapping_active_booking;
            """,
        ),
    ]
