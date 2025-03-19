from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models.acceptance_report import AcceptenceReport, CarPhoto, DocumentPhoto, KeyPhoto


@admin.register(AcceptenceReport)
class AcceptenceReportAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "vin",
        "reporter",
        "model",
        "place",
        "status",
        "report_number",
        "report_time",
        "acceptance_date",
    )
    list_filter = ("status", "reporter", "acceptance_date")
    search_fields = ("vin", "model", "place", "reporter__username")
    readonly_fields = ("report_number", "report_time", "acceptance_date")
    date_hierarchy = "acceptance_date"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).select_related("reporter")


@admin.register(CarPhoto)
class CarPhotoAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "report", "image", "created")
    list_filter = ("report", "created")
    search_fields = ("report__vin",)
    readonly_fields = ("created",)


@admin.register(KeyPhoto)
class KeyPhotoAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "report", "image", "created")
    list_filter = ("report", "created")
    search_fields = ("report__vin",)
    readonly_fields = ("created",)


@admin.register(DocumentPhoto)
class DocumentPhotoAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "report", "image", "created")
    list_filter = ("report", "created")
    search_fields = ("report__vin",)
    readonly_fields = ("created",)
