import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── ACCOUNTS ──────────────────────────────────────────────
def getAllUsers():
    return supabase.table("Accounts").select("*").execute().data

def appendUser(row: dict):
    supabase.table("Accounts").insert(row).execute()

def updateUser(user_id, updates: dict):
    supabase.table("Accounts").update(updates).eq("userId", user_id).execute()

def getNextUserId():
    users = getAllUsers()
    if not users:
        return 1
    return max(int(u["userId"]) for u in users) + 1

# ── LOGS ──────────────────────────────────────────────────
def getAllLogs():
    return supabase.table("Logs").select("*").execute().data

def appendLog(row: dict):
    supabase.table("Logs").insert(row).execute()

def updateLog(log_id, updates: dict):
    supabase.table("Logs").update(updates).eq("id", log_id).execute()

def deleteLog(log_id):
    supabase.table("Logs").delete().eq("id", log_id).execute()

# ── PROGRAMS ──────────────────────────────────────────────
def getAllProgram():
    return supabase.table("Programs").select("*").execute().data

def appendProgram(row: dict):
    supabase.table("Programs").insert(row).execute()

def updateProgram(program_id, updates: dict):
    supabase.table("Programs").update(updates).eq("id", program_id).execute()

def deleteProgram(program_id):
    supabase.table("Programs").delete().eq("id", program_id).execute()