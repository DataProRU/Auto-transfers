from django.contrib import admin

from autotrips.models.acceptance_report import AcceptenceReport, CarPhoto, DocumentPhoto, KeyPhoto


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
