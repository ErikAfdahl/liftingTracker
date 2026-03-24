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

def getUsers():
    creds = get_creds()
    client = gspread.authorize(creds)
    sheet = client.open("Accounts").sheet1
    return sheet

def getAllUsers(sheet):
    return sheet.get_all_records()

def appendUser(sheet, row: list):
    sheet.append_row(row)

def getNextUserId(users):
    if not users:
        return 1
    return max(int(u["userId"]) for u in users) + 1

def findUser(users, username, password):
    for user in users:
        if user["username"] == username and user["password"] == password:
            return user
    return None