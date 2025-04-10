from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations

ADMIN_FULLNAME = settings.ADMIN_FULLNAME
ADMIN_PHONE = settings.ADMIN_PHONE
ADMIN_TELEGRAM = settings.ADMIN_TELEGRAM
ADMIN_PASSWORD = settings.ADMIN_PASSWORD


def create_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    if not User.objects.filter(phone=ADMIN_PHONE).exists():
        User.objects.create(
            username="Admin",
            full_name=ADMIN_FULLNAME,
            phone=ADMIN_PHONE,
            telegram=ADMIN_TELEGRAM,
            password=make_password(ADMIN_PASSWORD),
            role="admin",
            is_approved=True,
            is_onboarded=True,
            is_superuser=True,
            is_staff=True,
        )


def delete_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(phone=ADMIN_PHONE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_user_tg_user_id"),
    ]

    operations = [
        migrations.RunPython(
            code=create_admin,
            reverse_code=delete_admin,
        ),
    ]
    