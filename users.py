import gspread
import os
from google.oauth2.service_account import Credentials

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(BASE_DIR, "credentials.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def getUsers():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
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