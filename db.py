import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── ACCOUNTS ──────────────────────────────────────────────
def getAllUsers():
    return supabase.table("accounts").select("*").execute().data

def appendUser(row: dict):
    supabase.table("accounts").insert(row).execute()

def updateUser(user_id, updates: dict):
    supabase.table("accounts").update(updates).eq("userId", user_id).execute()

def getNextUserId():
    users = getAllUsers()
    if not users:
        return 1
    return max(int(u["userId"]) for u in users) + 1

# ── LOGS ──────────────────────────────────────────────────
def getAllLogs():
    return supabase.table("logs").select("*").execute().data

def appendLog(row: dict):
    supabase.table("logs").insert(row).execute()

def updateLog(log_id, updates: dict):
    supabase.table("logs").update(updates).eq("id", log_id).execute()

def deleteLog(log_id):
    supabase.table("logs").delete().eq("id", log_id).execute()

# ── PROGRAMS ──────────────────────────────────────────────
def getAllProgram():
    return supabase.table("programs").select("*").execute().data

def appendProgram(row: dict):
    supabase.table("programs").insert(row).execute()

def updateProgram(program_id, updates: dict):
    supabase.table("programs").update(updates).eq("id", program_id).execute()

def deleteProgram(program_id):
    supabase.table("programs").delete().eq("id", program_id).execute()