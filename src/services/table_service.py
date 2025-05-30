import logging
from collections.abc import Callable
from typing import Any

from django.conf import settings
from gspread import Client, Spreadsheet, Worksheet, exceptions, service_account
from gspread.utils import ValueInputOption

logger = logging.getLogger(__name__)


class TableManager:
    def __init__(self, table_id: str, creds_path: str) -> None:
        self.table_id = table_id
        self.client = self._init_client(creds_path)
        self.table = self._open_table()

    @staticmethod
    def _init_client(creds_path: str) -> Client:
        return service_account(filename=creds_path)

    def _open_table(self) -> Spreadsheet:
        return self.client.open_by_key(self.table_id)

    def get_worksheet(self, title: str) -> Worksheet:
        return self.table.worksheet(title)

    def create_worksheet(self, title: str, rows: int, cols: int) -> Worksheet:
        return self.table.add_worksheet(title, rows, cols)

    def delete_worksheet(self, title: str) -> None:
        self.table.del_worksheet(self.get_worksheet(title))

    def insert_header(self, title: str, headers: list[str], rows: int, index: int = 1) -> None:
        cols_count = len(headers)
        try:
            worksheet = self.get_worksheet(title)
        except exceptions.WorksheetNotFound:
            worksheet = self.create_worksheet(title, rows, cols_count)

        header_values = worksheet.row_values(1)
        if len(header_values) == 0:
            worksheet.insert_row(headers, index=index)

    def append_row(self, title: str, data: list[Any]) -> None:
        worksheet = self.get_worksheet(title)
        worksheet.append_row(data, value_input_option=ValueInputOption.user_entered)

    def get_data_from_worksheet(self, title: str) -> list[dict[str, Any]]:
        worksheet = self.get_worksheet(title)
        return worksheet.get_all_records()

    def get_col_data_from_worksheet(self, title: str, col: int) -> list[Any]:
        worksheet = self.get_worksheet(title)
        return worksheet.col_values(col)


class DummyTableManager:
    """Заглушка для работы без реального подключения к таблицам."""

    def __init__(self) -> None:
        logger.warning("Using DummyTableManager - no real spreadsheet access")

    def __getattr__(self, name: str) -> Callable[[Any, Any], None]:
        def dummy_method(*_: Any, **__: Any) -> None:  # noqa: ANN401
            msg = f"DummyTableManager: {name} called but not configured"
            logger.warning(msg)

        return dummy_method


table_manager: TableManager | DummyTableManager
try:
    table_manager = TableManager(settings.TABLE_ID, settings.TABLE_CREDS)
except Exception as e:  # noqa: BLE001
    msg = f"TableManager initialization failed: {e}"
    logger.warning(msg)
    table_manager = DummyTableManager()


crm_table_manager: TableManager | DummyTableManager
try:
    crm_table_manager = TableManager(settings.CRM_TABLE_ID, settings.TABLE_CREDS)
except Exception as e:  # noqa: BLE001
    msg = f"CRMTableManager initialization failed: {e}"
    logger.warning(msg)
    crm_table_manager = DummyTableManager()
