from typing import Any

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.management.base import ArgumentParser, BaseCommand, CommandError
from django.db import transaction

from autotrips.models.vehicle_info import VehicleInfo, VehicleType

User = get_user_model()


class Command(BaseCommand):
    help = "Import VehicleInfo data from Excel file"

    EXCEL_COLUMNS = {
        "client_phone": "client_phone",
        "brand": "brand",
        "model": "model",
        "v_type": "v_type",
        "vin": "vin",
        "price": "price",
        "container_number": "container_number",
        "arrival_date": "arrival_date",
        "transporter": "transporter",
        "recipient": "recipient",
    }

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("file_path", type=str, help="Path to the Excel file")
        parser.add_argument("--sheet-name", type=str, default=0, help="Sheet name or index (default: 0)")
        parser.add_argument("--skip-rows", type=int, default=0, help="Number of rows to skip from the top (default: 0)")

    def handle(self, *args: tuple[Any], **options: dict[str, Any]) -> None:
        file_path = options["file_path"]
        sheet_name = options["sheet_name"]
        skip_rows = options["skip_rows"]

        try:
            vehicle_df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skip_rows)
            self.stdout.write(f"Successfully loaded {len(vehicle_df)} rows from {file_path}.")
            self.stdout.write(f"Available columns: {list(vehicle_df.columns)}.")

            missing_columns = [
                excel_column_name
                for excel_column_name in self.EXCEL_COLUMNS.values()
                if excel_column_name not in vehicle_df.columns
            ]

            if missing_columns:
                missing_columns_str = ", ".join(missing_columns)
                error_message = f"Missing required columns: {missing_columns_str}"
                raise CommandError(error_message)

            success_count = 0
            error_count = 0

            for index, row in vehicle_df.iterrows():
                try:
                    with transaction.atomic():
                        client_phone = str(row[self.EXCEL_COLUMNS["client_phone"]]).strip()
                        try:
                            client = User.objects.get(phone=client_phone)
                        except User.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Row {index + 1}: Client with phone {client_phone} not found. Skipping."
                                )
                            )
                            error_count += 1
                            continue

                        v_type_name = str(row[self.EXCEL_COLUMNS["v_type"]]).strip()
                        try:
                            v_type = VehicleType.objects.get(v_type=v_type_name)
                        except VehicleType.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Row {index + 1}: Vehicle type '{v_type_name}' not found. \
                                Skipping."
                                )
                            )
                            error_count += 1
                            continue

                        vehicle_data = {
                            "client": client,
                            "brand": str(row[self.EXCEL_COLUMNS["brand"]]).strip(),
                            "model": str(row[self.EXCEL_COLUMNS["model"]]).strip(),
                            "v_type": v_type,
                            "vin": str(row[self.EXCEL_COLUMNS["vin"]]).strip(),
                            "price": float(row[self.EXCEL_COLUMNS["price"]])
                            if pd.notna(row[self.EXCEL_COLUMNS["price"]])
                            else 0.0,
                            "container_number": str(row[self.EXCEL_COLUMNS["container_number"]]).strip(),
                            "arrival_date": pd.to_datetime(row[self.EXCEL_COLUMNS["arrival_date"]]).date(),
                            "transporter": str(row[self.EXCEL_COLUMNS["transporter"]]).strip(),
                            "recipient": str(row[self.EXCEL_COLUMNS["recipient"]]).strip(),
                        }

                        vehicle = VehicleInfo.objects.create(**vehicle_data)
                        success_count += 1

                        self.stdout.write(
                            f"Row {index + 1}: Created vehicle {vehicle.brand} {vehicle.model} (VIN: {vehicle.vin})"
                        )

                except Exception as e:  # noqa: BLE001
                    self.stdout.write(self.style.ERROR(f"Row {index + 1}: Error - {e!s}"))
                    error_count += 1
                    continue

            self.stdout.write(self.style.SUCCESS(f"Import completed! Success: {success_count}, Errors: {error_count}"))

        except FileNotFoundError as e:
            error_msg = f"File not found: {file_path}"
            raise CommandError(error_msg) from e
        except (pd.errors.EmptyDataError, pd.errors.ExcelFileError, pd.errors.ParserError) as e:
            error_msg = f"Error reading file: {e!s}"
            raise CommandError(error_msg) from e
