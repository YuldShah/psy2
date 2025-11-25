import gspread
import logging
import os
from datetime import datetime
from bot.config import GOOGLE_SHEETS_CREDENTIALS_PATH, GOOGLE_SHEET_ID

class GoogleSheets:
    def __init__(self, credentials_path: str = None, sheet_id: str = None):
        self.client = None
        self.sheet = None
        
        if credentials_path is None:
            credentials_path = GOOGLE_SHEETS_CREDENTIALS_PATH
        
        if sheet_id is None:
            sheet_id = GOOGLE_SHEET_ID
        
        if os.path.exists(credentials_path) and sheet_id:
            try:
                self.client = gspread.service_account(filename=credentials_path)
                self.sheet = self.client.open_by_key(sheet_id).sheet1
            except Exception as e:
                logging.error(f"Failed to connect to Google Sheets: {e}")
        else:
            logging.warning(f"Credentials file or Sheet ID missing. Google Sheets sync disabled.")

    def add_appointment(self, appt_id, student_name, student_id, date_str, time_str, reason, status):
        if not self.sheet:
            return
        
        try:
            self.sheet.append_row([appt_id, student_name, student_id, date_str, time_str, reason, status])
        except Exception as e:
            logging.error(f"Failed to add row to Sheets: {e}")

    def update_status(self, appt_id, new_status):
        if not self.sheet:
            return
            
        try:
            # Find row by ID (Column 1)
            cell = self.sheet.find(str(appt_id), in_column=1)
            if cell:
                # Update Status (Column 7)
                self.sheet.update_cell(cell.row, 7, new_status)
        except Exception as e:
            logging.error(f"Failed to update row in Sheets: {e}")

# Global instance
sheets_client = GoogleSheets()
