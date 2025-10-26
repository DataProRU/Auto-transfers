from typing import Any, cast

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from autotrips.models.managers import VehicleInfoManager

User = get_user_model()


class VehicleType(models.Model):
    v_type = models.CharField(_("Vehicle type"), max_length=100, unique=True, null=False, blank=False)

    class Meta:
        verbose_name = _("Vehicle type")
        verbose_name_plural = _("Vehicle types")

    def __str__(self) -> str:
        return cast(str, self.v_type)


class VehicleInfo(models.Model):
    class Statuses(models.TextChoices):
        INITIAL = "initial", _("Initial")
        LOADING = "loading", _("Loading")
        READY_FOR_TRANSPORT = "ready_for_transport", _("Ready for Transport")
        REQUIRES_APPROVAL = "requires_approval", _("Requires Approval")
        REJECTED = "rejected", _("Rejected")

    class TransitMethod(models.TextChoices):
        T1 = "t1", _("T1")
        RE_EXPORT = "re_export", _("Re-Export")
        WITHOUT_OPENNING = "without_openning", _("Without opening")

    class AcceptanceType(models.TextChoices):
        WITH_RE_EXPORT = "with_re_export", _("With re-export")
        WITHOUT_RE_EXPORT = "without_re_export", _("Without re-export")

    class TookTitle(models.TextChoices):
        YES = "yes", _("Yes")
        NO = "no", _("No")
        CONSIGNMENT = "consignment", _("Consignment")

    class InspectionDone(models.TextChoices):
        YES = "yes", _("Yes")
        NO = "no", _("No")
        REQUIRED_INSPECTION = "required_inspection", _("Required inspection")
        REQUIRED_EXPERTISE = "required_expertise", _("Required expertise")

    ################# CLIENT FIELDS #################
    client = models.ForeignKey(
        User, on_delete=models.RESTRICT, related_name="vehicles", null=False, blank=False, verbose_name=_("Client")
    )
    brand = models.CharField(_("Brand"), max_length=100, null=False, blank=False)
    model = models.CharField(_("Model"), max_length=100, null=False, blank=False)
    v_type = models.ForeignKey(
        VehicleType,
        on_delete=models.RESTRICT,
        related_name="vehicles",
        null=False,
        blank=False,
        verbose_name=_("Vehicle type"),
    )
    vin = models.CharField(
        _("VIN"),
        unique=True,
    )
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2, default=0, null=False, blank=False)
    container_number = models.CharField(_("Container number"), max_length=100, null=False, blank=False)
    arrival_date = models.DateField(_("Arrival date"), null=False, blank=False)
    transporter = models.CharField(_("Transporter"), max_length=100, null=False, blank=False)
    recipient = models.CharField(_("Recipient"), max_length=100, null=False, blank=False)
    comment = models.CharField(_("Comment"), max_length=255, null=True, blank=True)  # noqa: DJ001

    ################# LOGISTICIAN FIELDS #################
    transit_method = models.CharField(  # noqa: DJ001
        _("Transit method"), max_length=20, choices=TransitMethod.choices, null=True, blank=True
    )
    acceptance_type = models.CharField(  # noqa: DJ001
        _("Acceptance type"), max_length=20, choices=AcceptanceType.choices, null=True, blank=True
    )
    location = models.CharField(_("Location"), max_length=255, null=True, blank=True)  # noqa: DJ001
    requested_title = models.BooleanField(_("Requested title"), default=False)
    notified_parking = models.BooleanField(_("Notified parking"), default=False)
    notified_inspector = models.BooleanField(_("Notified inspector"), default=False)
    logistician_comment = models.CharField(_("Logistician comment"), max_length=255, null=True, blank=True)  # noqa: DJ001
    vehicle_transporter = models.ForeignKey(
        "VehicleTransporter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles",
        verbose_name=_("Vehicle transporter"),
    )
    logistician_keys_number = models.IntegerField(
        _("Logistician keys number"), validators=[MinValueValidator(0), MaxValueValidator(3)], null=True, blank=True
    )

    ################# OPENNING MANAGER FIELDS #################
    openning_date = models.DateField(_("Opening date"), null=True, blank=True)
    opened = models.BooleanField(_("Opened"), default=False)
    manager_comment = models.CharField(_("Manager comment"), max_length=255, null=True, blank=True)  # noqa: DJ001

    ################# TITLE FIELDS #################
    pickup_address = models.CharField(_("Pickup address"), max_length=255, null=True, blank=True)  # noqa: DJ001
    took_title = models.CharField(_("Took title"), max_length=20, choices=TookTitle.choices, null=True, blank=True)  # noqa: DJ001
    title_collection_date = models.DateField(_("Title collection date"), null=True, blank=True)

    ################# INSPECTOR FIELDS #################
    transit_number = models.CharField(_("Transit number"), max_length=20, null=True, blank=True)  # noqa: DJ001
    inspection_done = models.CharField(  # noqa: DJ001
        _("Inspection done"), max_length=20, choices=InspectionDone.choices, null=True, blank=True
    )
    inspection_date = models.DateField(_("Inspection date"), null=True, blank=True)
    number_sent = models.BooleanField(_("Number sent"), default=False)
    number_sent_date = models.DateField(_("Number sent date"), null=True, blank=True)
    inspection_paid = models.BooleanField(_("Inspection paid"), default=False)
    inspector_comment = models.CharField(_("Inspector comment"), max_length=255, null=True, blank=True)  # noqa: DJ001

    ################# RE-EXPORT FIELDS #################
    export = models.BooleanField(_("Export"), default=False)
    prepared_documents = models.BooleanField(_("Prepared documents"), default=False)

    ################# RECEIVER (ROLE USER) FIELDS #################
    vehicle_arrival_date = models.DateField(_("Vehicle arrival date"), null=True, blank=True)
    receive_vehicle = models.BooleanField(_("Receive vehicle"), default=False)
    receive_documents = models.BooleanField(_("Receive documents"), default=False)
    full_acceptance = models.BooleanField(_("Full acceptance"), default=False)
    receiver_keys_number = models.IntegerField(
        _("Receiver keys number"), validators=[MinValueValidator(0), MaxValueValidator(3)], null=True, blank=True
    )

    ################# TECHNICAL FIELDS #################
    approved_by_logistician = models.BooleanField(_("Approved by logistician"), default=False)
    approved_by_manager = models.BooleanField(_("Approved by manager"), default=False)
    approved_by_inspector = models.BooleanField(_("Approved by inspector"), default=False)
    approved_by_title = models.BooleanField(_("Approved by title"), default=False)
    approved_by_re_export = models.BooleanField(_("Approved by re-export"), default=False)
    approved_by_receiver = models.BooleanField(_("Approved by receiver"), default=False)
    ready_for_receiver = models.BooleanField(_("Ready for receiver"), default=False)
    status = models.CharField(_("Status"), max_length=20, choices=Statuses.choices, default=Statuses.INITIAL)
    status_changed = models.DateTimeField(_("Status changed"), default=timezone.now)
    creation_time = models.DateTimeField(_("Creation time"), default=timezone.now)

    objects = VehicleInfoManager()

    class Meta:
        verbose_name = _("Vehicle info")
        verbose_name_plural = _("Vehicle infos")

    def __str__(self) -> str:
        return f"{self.client.full_name}_{self.model}_{self.v_type}"

    def save(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> None:
        base_cls = type(self)
        if self.pk is not None:
            if self.status == base_cls.Statuses.INITIAL and self._has_all_required_approvals():
                self.status = base_cls.Statuses.LOADING

            self._track_status_change()

        super().save(*args, **kwargs)

    def _has_all_required_approvals(self) -> bool:
        base_cls = type(self)

        if self.transit_method == base_cls.TransitMethod.T1:
            return all([self.approved_by_logistician, self.approved_by_manager, self.approved_by_title])

        if self.transit_method == base_cls.TransitMethod.RE_EXPORT:
            return all(
                [
                    self.approved_by_logistician,
                    self.approved_by_manager,
                    self.approved_by_title,
                    self.approved_by_inspector,
                ]
            )

        if self.transit_method == base_cls.TransitMethod.WITHOUT_OPENNING:
            if self.acceptance_type == base_cls.AcceptanceType.WITH_RE_EXPORT:
                return all([self.approved_by_logistician, self.approved_by_title, self.approved_by_inspector])
            if self.acceptance_type == base_cls.AcceptanceType.WITHOUT_RE_EXPORT:
                return bool(self.approved_by_logistician)

        return False

    def _track_status_change(self) -> None:
        try:
            original = type(self).objects.get(pk=self.pk)
            if original.status != self.status:
                self.status_changed = timezone.now()
        except type(self).DoesNotExist:
            pass


class VehicleTransporter(models.Model):
    number = models.CharField(_("Number"), max_length=10, null=False, blank=False)

    class Meta:
        verbose_name = _("Vehicle transporter")
        verbose_name_plural = _("Vehicle transporters")

    def __str__(self) -> str:
        return str(self.number)
