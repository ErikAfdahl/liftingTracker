import gspread
import os
import json
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_creds():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        creds_dict = json.loads(creds_json)
        return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        # fallback for local development
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        CREDS_PATH = os.path.join(BASE_DIR, "credentials.json")
        return Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)

def getProgram():
    creds = get_creds()
    client = gspread.authorize(creds)
    sheet = client.open("Programs").sheet1
    return sheet

def getAllProgram(sheet):
    return sheet.get_all_records()

def appendProgram(sheet, row: list):
    sheet.append_row(row)