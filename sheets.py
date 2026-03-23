import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def getLogs():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("Logs").sheet1
    return sheet

@st.cache_data(ttl=60)
def getAllLogs(sheet):
    return sheet.get_all_records()

def appendLogs(sheet, row: list):
    sheet.append_row(row)