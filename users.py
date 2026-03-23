import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def getUsers():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("Accounts").sheet1
    return sheet

@st.cache_data(ttl=60)
def getAllUsers(_sheet):
    return _sheet.get_all_records()

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