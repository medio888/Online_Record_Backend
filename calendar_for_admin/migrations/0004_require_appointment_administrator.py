
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calendar_for_admin", "0003_protect_overlapping_appointments"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="appointment",
            name="administrator",
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="or_appointments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
