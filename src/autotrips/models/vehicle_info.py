import re
from typing import Any, cast

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
        INITIAL = "initial"
        LOADING = "loading"
        READY_FOR_TRANSPORT = "ready_for_transport"
        REQUIRES_APPROVAL = "requires_approval"
        REJECTED = "rejected"

    class TransitMethod(models.TextChoices):
        T1 = "t1"
        RE_EXPORT = "re_export"
        WITHOUT_OPENNING = "without_openning"

    class TookTitle(models.TextChoices):
        YES = "yes"
        NO = "no"
        CONSIGNMENT = "consignment"

    class InspectionDone(models.TextChoices):
        YES = "yes"
        NO = "no"
        REQUIRED_INSPECTION = "required_inspection"
        REQUIRED_EXPERTISE = "required_expertise"

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
    status = models.CharField(max_length=20, choices=Statuses.choices, default=Statuses.INITIAL)
    status_changed = models.DateTimeField(default=timezone.now)
    transit_method = models.CharField(max_length=20, choices=TransitMethod.choices, null=True, blank=True)  # noqa: DJ001
    location = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    requested_title = models.BooleanField(default=False)
    notified_parking = models.BooleanField(default=False)
    notified_inspector = models.BooleanField(default=False)
    logistician_comment = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    openning_date = models.DateField(null=True, blank=True)
    opened = models.BooleanField(default=False)
    manager_comment = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    pickup_address = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    took_title = models.CharField(max_length=20, choices=TookTitle.choices, null=True, blank=True)  # noqa: DJ001
    title_collection_date = models.DateField(null=True, blank=True)
    transit_number = models.CharField(max_length=20, null=True, blank=True)  # noqa: DJ001
    inspection_done = models.CharField(max_length=20, choices=InspectionDone.choices, null=True, blank=True)  # noqa: DJ001
    inspection_date = models.DateField(null=True, blank=True)
    number_sent = models.BooleanField(default=False)
    number_sent_date = models.DateField(null=True, blank=True)
    inspection_paid = models.BooleanField(default=False)
    inspector_comment = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    approved_by_logistician = models.BooleanField(default=False)
    approved_by_manager = models.BooleanField(default=False)
    approved_by_inspector = models.BooleanField(default=False)
    approved_by_title = models.BooleanField(default=False)
    approved_by_re_export = models.BooleanField(default=False)
    approved_by_receiver = models.BooleanField(default=False)
    notified_logistician_by_title = models.BooleanField(default=False)
    notified_logistician_by_inspector = models.BooleanField(default=False)
    creation_time = models.DateTimeField(default=timezone.now)

    objects = VehicleInfoManager()

    def __str__(self) -> str:
        return f"{self.client.full_name}_{self.model}_{self.v_type}"

    def save(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> None:
        if self.pk is not None:
            original = type(self).objects.get(pk=self.pk)
            if original.status != self.status:
                self.status_changed = timezone.now()
        super().save(*args, **kwargs)
