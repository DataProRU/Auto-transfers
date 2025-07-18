from typing import Any

from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from autotrips.models.acceptance_report import AcceptenceReport, CarPhoto, DocumentPhoto, KeyPhoto
from autotrips.models.vehicle_info import VehicleInfo, VehicleType


@admin.register(AcceptenceReport)
class AcceptenceReportAdmin(admin.ModelAdmin):
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
    search_fields = ("vin", "model")
    readonly_fields = ("report_number", "report_time", "acceptance_date")


@admin.register(CarPhoto)
class CarPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "report", "image", "created")
    list_filter = ("report", "created")
    search_fields = ("report__vin",)
    readonly_fields = ("created",)


@admin.register(KeyPhoto)
class KeyPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "report", "image", "created")
    list_filter = ("report", "created")
    search_fields = ("report__vin",)
    readonly_fields = ("created",)


@admin.register(DocumentPhoto)
class DocumentPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "report", "image", "created")
    list_filter = ("report", "created")
    search_fields = ("report__vin",)
    readonly_fields = ("created",)


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "v_type")
    list_filter = ("v_type",)
    search_fields = ("v_type",)
    ordering = ("v_type",)


@admin.register(VehicleInfo)
class VehicleInfoAdmin(admin.ModelAdmin):
    list_display = (
        "brand_model_type",
        "client_link",
        "vin",
        "arrival_date",
        "container_number",
        "status",
        "status_changed",
        "creation_time",
        "logistician_comment",
        "manager_comment",
    )
    list_filter = (
        "v_type",
        ("arrival_date", admin.DateFieldListFilter),
        ("creation_time", admin.DateFieldListFilter),
        ("status_changed", admin.DateFieldListFilter),
    )
    search_fields = ("brand", "model", "vin", "client__full_name", "client__phone")
    raw_id_fields = ("client",)
    date_hierarchy = "arrival_date"
    ordering = ("-arrival_date", "-creation_time")
    readonly_fields = ("creation_time", "status_changed")
    fieldsets = (
        (
            _("Vehicle Information"),
            {
                "fields": (
                    "brand",
                    "model",
                    "v_type",
                    "vin",
                )
            },
        ),
        (
            _("Logistics"),
            {
                "fields": (
                    "arrival_date",
                    "transporter",
                    "recipient",
                    "container_number",
                )
            },
        ),
        (_("Client & Status"), {"fields": ("client", "status", "status_changed", "comment")}),
        (
            _("CRM Information"),
            {
                "fields": (
                    "transit_method",
                    "location",
                    "requested_title",
                    "notified_parking",
                    "notified_inspector",
                    "logistician_comment",
                    "openning_date",
                    "opened",
                    "manager_comment",
                    "pickup_address",
                    "took_title",
                    "title_collection_date",
                    "transit_number",
                    "inspection_done",
                    "inspection_date",
                    "number_sent",
                    "number_sent_date",
                    "inspection_paid",
                    "inspector_comment",
                    "notified_logistician_by_title",
                    "notified_logistician_by_inspector",
                    "approved_by_logistician",
                    "approved_by_manager",
                    "approved_by_inspector",
                    "approved_by_title",
                    "approved_by_re_export",
                    "approved_by_receiver",
                )
            },
        ),
        (_("System Information"), {"fields": ("creation_time",), "classes": ("collapse",)}),
    )

    def brand_model_type(self, obj: models.Model) -> str:
        return f"{obj.brand} {obj.model} ({obj.v_type})"

    brand_model_type.short_description = _("Vehicle")  # type: ignore[attr-defined]
    brand_model_type.admin_order_field = "brand"  # type: ignore[attr-defined]

    def client_link(self, obj: models.Model) -> Any:  # noqa: ANN401
        url = reverse("admin:accounts_user_change", args=[obj.client.id])
        return format_html(f"<a href='{url}'>{obj.client.full_name} ({obj.client.phone})</a>")

    client_link.short_description = _("Client")  # type: ignore[attr-defined]
    client_link.admin_order_field = "client__full_name"  # type: ignore[attr-defined]
