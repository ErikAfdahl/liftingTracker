import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def getTokens():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("activeUsers").sheet1
    return sheet

def getAllTokens(sheet):
    return sheet.get_all_records()

def appendToken(sheet, row: list):
    sheet.append_row(row)