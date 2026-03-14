import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def getUsers():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("Accounts").sheet1
    return sheet

def getAllUsers(sheet):
    return sheet.get_all_records()

def appendUser(sheet, row: list):
    print(type(sheet))
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

# users = getUsers()
# all = getAllUsers(getUsers())
# appendUser(users, ["Erik", "poop", getNextUserId(all)])