# orders/google_sheets.py
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

'''''
class GoogleSheet:
    def __init__(self, key):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name("GOOGLE_APPLICATION_CREDENTIALS_JSON", scope)
        client = gspread.authorize(creds)
        self.sheet = client.open_by_key(key).sheet1
'''''
class GoogleSheet:
    def __init__(self, key):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        # Отримуємо JSON зі змінної середовища
        creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if not creds_json:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON not found in environment variables")

        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        self.sheet = client.open_by_key(key).sheet1
    def append_order(self, name, phone, product, source, date):
        self.sheet.append_row([name, phone, product, source, date])

    def read_all(self):
        return self.sheet.get_all_records()

    def update_cell(self, row, col, value):
        self.sheet.update_cell(row, col, value)
