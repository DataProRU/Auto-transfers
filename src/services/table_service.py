from typing import Any
import logging
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
    """Заглушка для работы без реального подключения к таблицам"""

    def __init__(self):
        logger.warning("Using DummyTableManager - no real spreadsheet access")

    def __getattr__(self, name):
        def dummy_method(*args, **kwargs):
            logger.warning(f"DummyTableManager: {name} called but not configured")

        return dummy_method

try:
    if settings.TABLE_ID and settings.TABLE_CREDS:
        table_manager = TableManager(settings.TABLE_ID, settings.TABLE_CREDS)
    else:
        raise ValueError("Missing table credentials")
except Exception as e:
    logger.warning(f"TableManager initialization failed: {e}")
    table_manager = DummyTableManager()
