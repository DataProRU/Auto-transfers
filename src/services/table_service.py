import os
from typing import Any

from gspread import Client, Spreadsheet, Worksheet, exceptions, service_account
from gspread.utils import ValueInputOption

TABLE_ID = os.getenv("TABLE_ID", "")
TABLE_CREDS = os.getenv("TABLE_CREDS", "")

g_client: Client = service_account(filename=TABLE_CREDS)


class TableManager:
    def __init__(self, table_id: str) -> None:
        self.table_id = table_id
        self.table: Spreadsheet = g_client.open_by_key(self.table_id)

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
        worksheet.insert_row(headers, index=index)

    def append_row(self, title: str, data: list[Any]) -> None:
        worksheet = self.get_worksheet(title)
        worksheet.append_row(data, value_input_option=ValueInputOption.user_entered)

    def get_data_from_worksheet(self, title: str) -> list[dict[str, Any]]:
        worksheet = self.get_worksheet(title)
        return worksheet.get_all_records()


table_manager = TableManager(TABLE_ID)
