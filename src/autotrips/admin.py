from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models.acceptance_report import AcceptanceReport, ReportPhoto


@admin.register(AcceptanceReport)
class AcceptanceReportAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "user",
        "report_number",
        "created",
        "updated",
    )
    list_filter = ("user", "created")
    search_fields = ("report_number", "user__username")
    readonly_fields = ("report_number", "created", "updated")
    date_hierarchy = "created"

    def get_queryset(self, request: HttpRequest) -> QuerySet[AcceptanceReport]:
        return super().get_queryset(request).select_related("user")


@admin.register(ReportPhoto)
class ReportPhotoAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "report", "type", "photo", "created")
    list_filter = ("report", "type", "created")
    search_fields = ("report__report_number",)
    readonly_fields = ("created",)
