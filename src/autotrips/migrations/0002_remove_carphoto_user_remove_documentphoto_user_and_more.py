# Generated by Django 5.1.6 on 2025-03-15 11:11

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("autotrips", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="carphoto",
            name="user",
        ),
        migrations.RemoveField(
            model_name="documentphoto",
            name="user",
        ),
        migrations.RemoveField(
            model_name="keyphoto",
            name="user",
        ),
        migrations.AddField(
            model_name="carphoto",
            name="report",
            field=models.ForeignKey(
                default=4,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="car_photos",
                to="autotrips.acceptencereport",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="documentphoto",
            name="report",
            field=models.ForeignKey(
                default="4",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="doc_photos",
                to="autotrips.acceptencereport",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="keyphoto",
            name="report",
            field=models.ForeignKey(
                default=4,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="key_photos",
                to="autotrips.acceptencereport",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="acceptencereport",
            name="acceptance_date",
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]
