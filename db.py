import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TEMPLATE_USER_ID = 19

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

def getTemplateProgramData():
    prog_data = getAllProgram()
    return [row for row in prog_data if str(row["userId"]) == str(TEMPLATE_USER_ID)]

def getUserLogs(user_id):
    data = supabase.table("Logs").select("*").eq("userId", user_id) \
        .order("date", desc=True).order("id", desc=True).limit(1000).execute().data
    return list(reversed(data))

def getUserLogsByExercise(user_id, program, exercise, set_num):
    return (supabase.table("Logs")
            .select("*")
            .eq("userId", user_id)
            .eq("program", program)
            .eq("exerciseName", exercise)
            .eq("setNum", set_num)
            .order("date", desc=False)
            .order("id", desc=False)
            .execute().data)

def getUserLogsByDates(user_id, program, date_last, date_prev):
    return (supabase.table("Logs")
            .select("*")
            .eq("userId", user_id)
            .eq("program", program)
            .in_("date", [date_last, date_prev])
            .execute().data)

def getAllLogs():
    return supabase.table("Logs").select("*").limit(10000).execute().data

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