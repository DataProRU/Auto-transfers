from typing import TYPE_CHECKING, Any, cast

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.management.base import ArgumentParser, BaseCommand, CommandError
from django.db import transaction

from autotrips.models.vehicle_info import VehicleInfo, VehicleType

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as UserModel
else:
    UserModel = get_user_model()


class Command(BaseCommand):
    help = "Import VehicleInfo data from Excel file"

    EXCEL_COLUMNS = {
        "client_phone": "Номер телефона клиента",
        "year_brand_model": "Год Марка Модель",
        "v_type": "Тип ТС",
        "vin": "VIN номер",
        "price": "Цена",
        "container_number": "№ контейнера",
        "arrival_date": "Дата прибытия контейнера",
        "transporter": "Перевозчик",
        "recipient": "Получатель",
        "comment": "Комментарий",
    }

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("file_path", type=str, help="Path to the Excel file")
        parser.add_argument("--sheet-name", type=str, default=0, help="Sheet name or index (default: 0)")
        parser.add_argument("--skip-rows", type=int, default=0, help="Number of rows to skip from the top (default: 0)")

    def handle(self, *args: tuple[Any], **options: dict[str, Any]) -> None:
        file_path = cast(str, options["file_path"])
        sheet_name = cast(str | int, options["sheet_name"])
        skip_rows = cast(int, options["skip_rows"])

        try:
            vehicle_df = self._load_excel_file(file_path, sheet_name, skip_rows)
            self._check_required_columns(vehicle_df)

            success_count, error_count = self._process_vehicles(vehicle_df)

            self.stdout.write(self.style.SUCCESS(f"Import completed! Success: {success_count}, Errors: {error_count}"))

        except FileNotFoundError as e:
            error_msg = f"File not found: {file_path}"
            raise CommandError(error_msg) from e
        except (pd.errors.EmptyDataError, pd.errors.ClosedFileError, pd.errors.ParserError) as e:
            error_msg = f"Error reading file: {e!s}"
            raise CommandError(error_msg) from e

    def _load_excel_file(self, file_path: str, sheet_name: str | int, skip_rows: int) -> pd.DataFrame:
        vehicle_df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skip_rows)
        self.stdout.write(f"Successfully loaded {len(vehicle_df)} rows from {file_path}.")
        self.stdout.write(f"Available columns: {list(vehicle_df.columns)}.")
        return vehicle_df

    def _process_vehicles(self, vehicle_df: pd.DataFrame) -> tuple[int, int]:
        success_count = 0
        error_count = 0

        for index, row in vehicle_df.iterrows():
            try:
                with transaction.atomic():
                    client = self._get_client(row, index)
                    if not client:
                        error_count += 1
                        continue

                    vehicle_data = self._build_vehicle_data(row, client)
                    vehicle = VehicleInfo.objects.create(**vehicle_data)
                    success_count += 1

                    self.stdout.write(
                        f"Row {index + 1}: Created vehicle {vehicle.year_brand_model} (VIN: {vehicle.vin})"
                    )

            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.ERROR(f"Row {index + 1}: Error - {e!s}"))
                error_count += 1

        return success_count, error_count

    def _get_client(self, row: pd.Series, index: int) -> UserModel | None:
        client_phone = f"+{str(row[self.EXCEL_COLUMNS['client_phone']]).strip()}"
        try:
            return UserModel.objects.get(phone=client_phone)
        except UserModel.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f"Row {index + 1}: Client with phone {client_phone} not found. Skipping.")
            )
            return None

    def _build_vehicle_data(self, row: pd.Series, client: UserModel) -> dict[str, Any]:
        vehicle_data = {
            "client": client,
            "year_brand_model": str(row[self.EXCEL_COLUMNS["year_brand_model"]]).strip(),
            "vin": str(row[self.EXCEL_COLUMNS["vin"]]).strip(),
        }

        # Optional fields
        self._add_optional_v_type(vehicle_data, row)
        self._add_optional_price(vehicle_data, row)
        self._add_optional_container_number(vehicle_data, row)
        self._add_optional_arrival_date(vehicle_data, row)
        self._add_optional_transporter(vehicle_data, row)
        self._add_optional_recipient(vehicle_data, row)
        self._add_optional_comment(vehicle_data, row)

        return vehicle_data

    def _add_optional_v_type(self, vehicle_data: dict[str, Any], row: pd.Series) -> None:
        if pd.notna(row[self.EXCEL_COLUMNS["v_type"]]) and str(row[self.EXCEL_COLUMNS["v_type"]]).strip():
            v_type_name = str(row[self.EXCEL_COLUMNS["v_type"]]).strip()
            try:
                vehicle_data["v_type"] = VehicleType.objects.get(v_type=v_type_name)
            except VehicleType.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Vehicle type '{v_type_name}' not found. Creating without v_type.")
                )

    def _add_optional_price(self, vehicle_data: dict[str, Any], row: pd.Series) -> None:
        if pd.notna(row[self.EXCEL_COLUMNS["price"]]) and row[self.EXCEL_COLUMNS["price"]] != "":
            vehicle_data["price"] = float(row[self.EXCEL_COLUMNS["price"]])

    def _add_optional_container_number(self, vehicle_data: dict[str, Any], row: pd.Series) -> None:
        if (
            pd.notna(row[self.EXCEL_COLUMNS["container_number"]])
            and str(row[self.EXCEL_COLUMNS["container_number"]]).strip()
        ):
            vehicle_data["container_number"] = str(row[self.EXCEL_COLUMNS["container_number"]]).strip()

    def _add_optional_arrival_date(self, vehicle_data: dict[str, Any], row: pd.Series) -> None:
        if pd.notna(row[self.EXCEL_COLUMNS["arrival_date"]]) and row[self.EXCEL_COLUMNS["arrival_date"]] != "":
            vehicle_data["arrival_date"] = pd.to_datetime(row[self.EXCEL_COLUMNS["arrival_date"]]).date()

    def _add_optional_transporter(self, vehicle_data: dict[str, Any], row: pd.Series) -> None:
        if pd.notna(row[self.EXCEL_COLUMNS["transporter"]]) and str(row[self.EXCEL_COLUMNS["transporter"]]).strip():
            vehicle_data["transporter"] = str(row[self.EXCEL_COLUMNS["transporter"]]).strip()

    def _add_optional_recipient(self, vehicle_data: dict[str, Any], row: pd.Series) -> None:
        if pd.notna(row[self.EXCEL_COLUMNS["recipient"]]) and str(row[self.EXCEL_COLUMNS["recipient"]]).strip():
            vehicle_data["recipient"] = str(row[self.EXCEL_COLUMNS["recipient"]]).strip()

    def _add_optional_comment(self, vehicle_data: dict[str, Any], row: pd.Series) -> None:
        if pd.notna(row[self.EXCEL_COLUMNS["comment"]]) and str(row[self.EXCEL_COLUMNS["comment"]]).strip():
            vehicle_data["comment"] = str(row[self.EXCEL_COLUMNS["comment"]]).strip()

    def _check_required_columns(self, vehicle_df: pd.DataFrame) -> None:
        missing_columns = [
            excel_column_name
            for excel_column_name in self.EXCEL_COLUMNS.values()
            if excel_column_name not in vehicle_df.columns
        ]
        if missing_columns:
            missing_columns_str = ", ".join(missing_columns)
            error_message = f"Missing required columns: {missing_columns_str}"
            raise CommandError(error_message)
