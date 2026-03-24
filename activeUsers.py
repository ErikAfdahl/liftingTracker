import gspread
import os
from google.oauth2.service_account import Credentials

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(BASE_DIR, "credentials.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def getTokens():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("activeUsers").sheet1
    return sheet

def getAllTokens(sheet):
    return sheet.get_all_records()

def appendToken(sheet, row: list):
    sheet.append_row(row)