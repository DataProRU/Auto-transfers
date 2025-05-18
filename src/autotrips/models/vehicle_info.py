import re
from typing import cast

from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from autotrips.models.managers import VehicleInfoManager

User = get_user_model()


class VehicleType(models.Model):
    v_type = models.CharField(max_length=100, unique=True, null=False, blank=False)

    def __str__(self) -> str:
        return cast(str, self.v_type)


class VehicleInfo(models.Model):
    class Statuses(models.TextChoices):
        NEW = "Новый"

    client = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="vehicles", null=False, blank=False)
    brand = models.CharField(max_length=100, null=False, blank=False)
    model = models.CharField(max_length=100, null=False, blank=False)
    v_type = models.ForeignKey(VehicleType, on_delete=models.RESTRICT, related_name="vehicles", null=False, blank=False)
    vin = models.CharField(
        unique=True,
        validators=[RegexValidator(regex=re.compile(r"^[A-HJ-NPR-Z0-9]{17}$"), message="Invalid vin format.")],
    )
    container_number = models.CharField(max_length=100, null=False, blank=False)
    arrival_date = models.DateField(null=False, blank=False)
    transporter = models.CharField(max_length=100, null=False, blank=False)
    recipient = models.CharField(max_length=100, null=False, blank=False)
    comment = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    status = models.CharField(max_length=10, choices=Statuses.choices, default=Statuses.NEW)
    status_changed = models.DateTimeField(default=timezone.now)
    creation_time = models.DateTimeField(default=timezone.now)

    objects = VehicleInfoManager()

    def __str__(self) -> str:
        return f"{self.client.full_name}_{self.model}_{self.v_type}"
