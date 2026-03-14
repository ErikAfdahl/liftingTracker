import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def getLogs():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("Logs").sheet1
    return sheet

def getAllLogs(sheet):
    print(type(sheet))
    return sheet.get_all_records()

def appendLogs(sheet, row: list):
    sheet.append_row(row)

# Make sure `"Gainz Tracker"` matches the **exact name** of your Google Sheet.
#
# Once you've got that file saved, run this in your terminal to test the connection:
#
# python -c "from sheets import getLogs; s = getLogs(); print('Connected!')"

# sheet = getLogs()
# appendLogs(sheet, [1, "push", "3/11/26", "bench", 1, 200.0, 6, 240, 0])
# print(getAllLogs(sheet))


# program	date	exerciseName	setNum	weight	reps	1rm	diff