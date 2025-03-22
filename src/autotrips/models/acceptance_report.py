import re
from typing import Any

from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class AcceptenceReport(models.Model):
    class Statuses(models.TextChoices):
        SUCCESS = "Принят"
        FAILED = "Повреждён"

    vin = models.CharField(
        validators=[RegexValidator(regex=re.compile(r"^[A-HJ-NPR-Z0-9]{17}$"), message="Invalid vin format.")]
    )
    reporter = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="reports", null=False, blank=False)
    model = models.CharField(max_length=100, null=False, blank=False)
    place = models.CharField(max_length=100, null=False, blank=False)
    comment = models.CharField(max_length=255, null=False, blank=False)
    report_number = models.IntegerField(null=False, blank=False, default=1)
    report_time = models.DateTimeField(default=timezone.now)
    acceptance_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=Statuses.choices, default=Statuses.SUCCESS)

    def __str__(self) -> str:
        return f"{self.reporter.full_name}_{self.model}_{self.acceptance_date}"

    def save(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> None:
        if not self.pk:
            last_report = AcceptenceReport.objects.filter(vin=self.vin).order_by("-report_number").first()
            if last_report:
                self.report_number = last_report.report_number + 1

        super().save(*args, **kwargs)


class CarPhoto(models.Model):
    report = models.ForeignKey(AcceptenceReport, on_delete=models.CASCADE, related_name="car_photos")
    image = models.ImageField(upload_to="cars/%Y/%m/%d/")
    created = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.report.model}_car_{self.created}"


class KeyPhoto(models.Model):
    report = models.ForeignKey(AcceptenceReport, on_delete=models.CASCADE, related_name="key_photos")
    image = models.ImageField(upload_to="keys/%Y/%m/%d/")
    created = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.report.model}_key_{self.created}"


class DocumentPhoto(models.Model):
    report = models.ForeignKey(AcceptenceReport, on_delete=models.CASCADE, related_name="document_photos")
    image = models.ImageField(upload_to="car-docs/%Y/%m/%d/")
    created = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.report.model}_document_{self.created}"
