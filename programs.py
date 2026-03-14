import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def getProgram():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("Programs").sheet1
    return sheet

def getAllProgram(sheet):
    return sheet.get_all_records()

def appendProgram(sheet, row: list):
    sheet.append_row(row)

# Make sure `"Gainz Tracker"` matches the **exact name** of your Google Sheet.
#
# Once you've got that file saved, run this in your terminal to test the connection:
#
# python -c "from sheets import getProgram; s = getProgram(); print('Connected!')"

# sheet = getProgram()
# print(getAllProgram(sheet))