import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def getProgram():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("Programs").sheet1
    return sheet

@st.cache_data(ttl=60)
def getAllProgram(_sheet):
    return _sheet.get_all_records()

def appendProgram(sheet, row: list):
    sheet.append_row(row)