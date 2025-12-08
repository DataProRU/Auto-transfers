from typing import Any

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from autotrips.models.vehicle_info import VehicleInfo

User = get_user_model()


class AcceptenceReport(models.Model):
    class Statuses(models.TextChoices):
        SUCCESS = "Принят", _("Accepted")
        FAILED = "Повреждён", _("Damaged")

    reporter = models.ForeignKey(
        User, on_delete=models.RESTRICT, related_name="reports", null=False, blank=False, verbose_name=_("Reporter")
    )
    vehicle = models.ForeignKey(
        VehicleInfo,
        on_delete=models.CASCADE,
        related_name="reports",
        null=False,
        blank=False,
        verbose_name=_("Vehicle"),
    )
    place = models.CharField(_("Place"), max_length=100, blank=True, default="")
    comment = models.CharField(_("Comment"), max_length=255, blank=True, default="")
    report_number = models.IntegerField(_("Report number"), null=False, blank=False, default=1)
    report_time = models.DateTimeField(_("Report time"), default=timezone.now)
    acceptance_date = models.DateField(_("Acceptance date"), default=timezone.localdate)
    status = models.CharField(_("Status"), max_length=10, choices=Statuses.choices, default=Statuses.SUCCESS)

    class Meta:
        verbose_name = _("Acceptance report")
        verbose_name_plural = _("Acceptance reports")

    def __str__(self) -> str:
        return f"{self.reporter.full_name}_{self.vehicle.brand}_{self.vehicle.model}_{self.acceptance_date}"

    def save(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> None:
        if not self.pk:
            last_report = AcceptenceReport.objects.filter(vehicle=self.vehicle).order_by("-report_number").first()
            if last_report:
                self.report_number = last_report.report_number + 1

        super().save(*args, **kwargs)


class CarPhoto(models.Model):
    report = models.ForeignKey(
        AcceptenceReport, on_delete=models.CASCADE, related_name="car_photos", verbose_name=_("Report")
    )
    image = models.ImageField(_("Image"), upload_to="cars/%Y/%m/%d/")
    created = models.DateTimeField(_("Created"), default=timezone.now)

    class Meta:
        verbose_name = _("Car photo")
        verbose_name_plural = _("Car photos")

    def __str__(self) -> str:
        return f"{self.report.vehicle.brand}_{self.report.vehicle.model}_car_{self.created}"


class KeyPhoto(models.Model):
    report = models.ForeignKey(
        AcceptenceReport, on_delete=models.CASCADE, related_name="key_photos", verbose_name=_("Report")
    )
    image = models.ImageField(_("Image"), upload_to="keys/%Y/%m/%d/")
    created = models.DateTimeField(_("Created"), default=timezone.now)

    class Meta:
        verbose_name = _("Key photo")
        verbose_name_plural = _("Key photos")

    def __str__(self) -> str:
        return f"{self.report.vehicle.brand}_{self.report.vehicle.model}_key_{self.created}"


class DocumentPhoto(models.Model):
    report = models.ForeignKey(
        AcceptenceReport, on_delete=models.CASCADE, related_name="document_photos", verbose_name=_("Report")
    )
    image = models.ImageField(_("Image"), upload_to="car-docs/%Y/%m/%d/")
    created = models.DateTimeField(_("Created"), default=timezone.now)

    class Meta:
        verbose_name = _("Vehicle document photo")
        verbose_name_plural = _("Vehicle document photos")

    def __str__(self) -> str:
        return f"{self.report.vehicle.brand}_{self.report.vehicle.model}_document_{self.created}"
