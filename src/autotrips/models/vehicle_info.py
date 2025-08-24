import re
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
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

    ################# CLIENT FIELDS #################
    client = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="vehicles", null=False, blank=False)
    brand = models.CharField(max_length=100, null=False, blank=False)
    model = models.CharField(max_length=100, null=False, blank=False)
    v_type = models.ForeignKey(VehicleType, on_delete=models.RESTRICT, related_name="vehicles", null=False, blank=False)
    vin = models.CharField(
        unique=True,
        validators=[RegexValidator(regex=re.compile(r"^[A-HJ-NPR-Z0-9]{17}$"), message="Invalid vin format.")],
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=False, blank=False)
    container_number = models.CharField(max_length=100, null=False, blank=False)
    arrival_date = models.DateField(null=False, blank=False)
    transporter = models.CharField(max_length=100, null=False, blank=False)
    recipient = models.CharField(max_length=100, null=False, blank=False)
    comment = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001

    ################# LOGISTICIAN FIELDS #################
    transit_method = models.CharField(max_length=20, choices=TransitMethod.choices, null=True, blank=True)  # noqa: DJ001
    location = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    requested_title = models.BooleanField(default=False)
    notified_parking = models.BooleanField(default=False)
    notified_inspector = models.BooleanField(default=False)
    logistician_comment = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    vehicle_transporter = models.ForeignKey(
        "VehicleTransporter", on_delete=models.SET_NULL, null=True, blank=True, related_name="vehicles"
    )
    logistician_keys_number = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(3)], null=True, blank=True
    )

    ################# OPENNING MANAGER FIELDS #################
    openning_date = models.DateField(null=True, blank=True)
    opened = models.BooleanField(default=False)
    manager_comment = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001

    ################# TITLE FIELDS #################
    pickup_address = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    took_title = models.CharField(max_length=20, choices=TookTitle.choices, null=True, blank=True)  # noqa: DJ001
    title_collection_date = models.DateField(null=True, blank=True)
    notified_logistician_by_title = models.BooleanField(default=False)

    ################# INSPECTOR FIELDS #################
    transit_number = models.CharField(max_length=20, null=True, blank=True)  # noqa: DJ001
    inspection_done = models.CharField(max_length=20, choices=InspectionDone.choices, null=True, blank=True)  # noqa: DJ001
    inspection_date = models.DateField(null=True, blank=True)
    number_sent = models.BooleanField(default=False)
    number_sent_date = models.DateField(null=True, blank=True)
    inspection_paid = models.BooleanField(default=False)
    inspector_comment = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    notified_logistician_by_inspector = models.BooleanField(default=False)

    ################# RE-EXPORT FIELDS #################
    export = models.BooleanField(default=False)
    prepared_documents = models.BooleanField(default=False)

    ################# RECEIVER (ROLE USER) FIELDS #################
    vehicle_arrival_date = models.DateField(null=True, blank=True)
    receive_vehicle = models.BooleanField(default=False)
    receive_documents = models.BooleanField(default=False)
    full_acceptance = models.BooleanField(default=False)
    receiver_keys_number = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(3)], null=True, blank=True
    )

    ################# TECHNICAL FIELDS #################
    approved_by_logistician = models.BooleanField(default=False)
    approved_by_manager = models.BooleanField(default=False)
    approved_by_inspector = models.BooleanField(default=False)
    approved_by_title = models.BooleanField(default=False)
    approved_by_re_export = models.BooleanField(default=False)
    approved_by_receiver = models.BooleanField(default=False)
    ready_for_receiver = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Statuses.choices, default=Statuses.INITIAL)
    status_changed = models.DateTimeField(default=timezone.now)
    creation_time = models.DateTimeField(default=timezone.now)

    objects = VehicleInfoManager()

    def __str__(self) -> str:
        return f"{self.client.full_name}_{self.model}_{self.v_type}"

    def save(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> None:
        if self.pk is not None:
            approvals_map = {
                type(self).TransitMethod.T1: [
                    self.approved_by_logistician,
                    self.approved_by_manager,
                    self.approved_by_title,
                ],
                type(self).TransitMethod.RE_EXPORT: [
                    self.approved_by_logistician,
                    self.approved_by_manager,
                    self.approved_by_title,
                    self.approved_by_inspector,
                ],
                type(self).TransitMethod.WITHOUT_OPENNING: [
                    self.approved_by_logistician,
                    self.approved_by_title,
                    self.approved_by_inspector,
                ],
            }

            if self.status == type(self).Statuses.INITIAL:
                required_approvals = approvals_map.get(self.transit_method)
                if required_approvals and all(required_approvals):
                    self.status = type(self).Statuses.LOADING

            original = type(self).objects.get(pk=self.pk)
            if original.status != self.status:
                self.status_changed = timezone.now()
        super().save(*args, **kwargs)


class VehicleTransporter(models.Model):
    number = models.CharField(max_length=10, null=False, blank=False)

    def __str__(self) -> str:
        return f"transporter_{self.number}"
