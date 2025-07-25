# Generated by Django 5.1.7 on 2025-07-17 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("autotrips", "0005_vehicleinfo_approved_by_inspector_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicleinfo",
            name="notified_logistician_by_inspector",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vehicleinfo",
            name="notified_logistician_by_title",
            field=models.BooleanField(default=False),
        ),
    ]
