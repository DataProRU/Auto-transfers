from typing import Any

from django.conf import settings
from django.db.models.signals import post_save
from django.utils import timezone

from autotrips.models.acceptance_report import AcceptenceReport
from services.table_service import table_manager


class PostReportSaveSignalReciever:
    WORKSHEET = settings.REPORTS_WORKSHEET
    URL = settings.FRONTEND_URL

    def build_data_to_table(self, report: AcceptenceReport) -> list[str]:
        report_time_local = timezone.localtime(report.report_time)
        report_time = report_time_local.strftime("%d.%m.%Y %H:%M:%S")
        acceptance_date = report.acceptance_date.strftime("%d.%m.%Y")
        reporter = report.reporter
        car_photos = f"{self.URL}reports/{report.id}/car-photos"  # replace with frontend url
        key_photos = f"{self.URL}reports/{report.id}/key-photos"
        doc_photos = f"{self.URL}reports/{report.id}/doc-photos"

        return [
            report_time,
            reporter.phone,
            reporter.full_name,
            report.report_number,
            acceptance_date,
            report.vin,
            report.model,
            car_photos,
            key_photos,
            doc_photos,
            report.place,
            report.comment,
            report.status,
        ]

    def __call__(
        self,
        sender: AcceptenceReport,
        instance: AcceptenceReport,
        created: bool,
        **kwargs: dict[str, Any],  # noqa: FBT001
    ) -> None:
        if created:
            row = self.build_data_to_table(instance)
            table_manager.append_row(self.WORKSHEET, row)  # replace with celery task


reciever = PostReportSaveSignalReciever()
post_save.connect(receiver=reciever, sender=AcceptenceReport)
