"""Модели для работы с отчетами о приемке."""

from collections.abc import Iterable

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.utils import timezone

from accounts.models.user import User


def validate_file_size(value: UploadedFile) -> None:
    """Валидация размера файла."""
    filesize = value.size
    if filesize is None:
        raise ValidationError("Размер файла не может быть пустым")
    if filesize > 10 * 1024 * 1024:  # 10MB
        raise ValidationError("Максимальный размер файла 10MB")


class AcceptanceReport(models.Model):
    """Модель отчета о приемке."""

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

    objects = models.Manager["AcceptanceReport"]()

    class Meta:
        verbose_name = "Отчет о приемке"
        verbose_name_plural = "Отчеты о приемке"
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["-created"]),
            models.Index(fields=["user", "-report_number"]),
        ]

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
            max_report = AcceptanceReport.objects.filter(user=self.user).order_by("-report_number").first()
            self.report_number = max_report.report_number + 1 if max_report else 1
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class ReportPhoto(models.Model):
    """Модель для хранения фотографий отчета."""

    class PhotoTypes(models.TextChoices):
        """Типы фотографий отчета."""

        MAIN = "main", "Основное фото"
        CAR = "car", "Фото автомобиля"
        KEY = "key", "Фото ключей"
        DOCUMENT = "document", "Фото документов"

    report = models.ForeignKey(
        AcceptanceReport,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name="Отчет",
    )
    photo = models.ImageField(
        upload_to="report_photos/",
        validators=[validate_file_size],
        verbose_name="Фотография",
    )
    type = models.CharField(
        max_length=20,
        choices=PhotoTypes.choices,
        verbose_name="Тип фотографии",
    )
    created = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания",
    )

    class Meta:
        verbose_name = "Фотография отчета"
        verbose_name_plural = "Фотографии отчета"
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["-created"]),
        ]

    def __str__(self) -> str:
        return f"{self.report.report_number}_{self.type}_{self.created}"
