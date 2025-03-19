from collections.abc import Iterable

from django.db import models
from django.utils import timezone

from accounts.models.user import User


class AcceptenceReport(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="acceptance_reports",
        verbose_name="Пользователь",
    )
    report_number = models.IntegerField(
        verbose_name="Номер отчета",
        help_text="Номер отчета в системе",
    )
    created = models.DateTimeField(
        verbose_name="Дата создания",
        default=timezone.now,
    )
    updated = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True,
    )
    photo_1 = models.ImageField(
        upload_to="acceptance_reports",
        verbose_name="Фото 1",
    )
    photo_2 = models.ImageField(
        upload_to="acceptance_reports",
        verbose_name="Фото 2",
    )
    photo_3 = models.ImageField(
        upload_to="acceptance_reports",
        verbose_name="Фото 3",
    )

    objects = models.Manager["AcceptenceReport"]()

    class Meta:
        verbose_name = "Отчет о приемке"
        verbose_name_plural = "Отчеты о приемке"
        ordering = ["-created"]

    def __str__(self) -> str:
        return f"Отчет №{self.report_number} от {self.created.date()}"

    def save(
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        if not self.pk:
            max_report = AcceptenceReport.objects.filter(user=self.user).order_by("-report_number").first()
            self.report_number = max_report.report_number + 1 if max_report else 1
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class CarPhoto(models.Model):
    report = models.ForeignKey(AcceptenceReport, on_delete=models.CASCADE, related_name="car_photos")
    photo = models.ImageField(upload_to="car_photos/")
    created = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.report.report_number}_car_{self.created}"


class KeyPhoto(models.Model):
    report = models.ForeignKey(AcceptenceReport, on_delete=models.CASCADE, related_name="key_photos")
    photo = models.ImageField(upload_to="key_photos/")
    created = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.report.report_number}_key_{self.created}"


class DocumentPhoto(models.Model):
    report = models.ForeignKey(AcceptenceReport, on_delete=models.CASCADE, related_name="document_photos")
    photo = models.ImageField(upload_to="document_photos/")
    created = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.report.report_number}_document_{self.created}"
