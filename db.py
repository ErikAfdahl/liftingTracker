import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TEMPLATE_USER_ID = 19

# ── ACCOUNTS ──────────────────────────────────────────────
def getAllUsers():
    return supabase.table("accounts").select("*").execute().data

def appendUser(row: dict):
    supabase.table("accounts").insert(row).execute()

def updateUser(user_id, updates: dict):
    supabase.table("accounts").update(updates).eq("user_id", user_id).execute()

def getNextUserId():
    users = getAllUsers()
    if not users:
        return 1
    return max(int(u["user_id"]) for u in users) + 1

# ── LOGS ──────────────────────────────────────────────────

def getTemplateProgramData():
    prog_data = getAllExercises()
    return [row for row in prog_data if str(row["user_id"]) == str(TEMPLATE_USER_ID)]

def getUserLogs(user_id):
    data = supabase.table("logs").select("*").eq("user_id", user_id) \
        .order("date", desc=True).order("id", desc=True).limit(1000).execute().data
    return list(reversed(data))

def getUserLogsByExercise(user_id, program, exercise, set_num):
    return (supabase.table("logs")
            .select("*")
            .eq("user_id", user_id)
            .eq("program_name", program)
            .eq("exercise_name", exercise)
            .eq("set_num", set_num)
            .order("date", desc=False)
            .order("id", desc=False)
            .execute().data)

def getUserLogsByDates(user_id, program, date_last, date_prev):
    return (supabase.table("logs")
            .select("*")
            .eq("user_id", user_id)
            .eq("program", program)
            .in_("date", [date_last, date_prev])
            .execute().data)

def getUserLogsUnactive(user_id):
    return (supabase.table("logs")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", 0)
            .execute().data)

def getAllLogs():
    return supabase.table("logs").select("*").limit(10000).execute().data

def appendLog(row: dict):
    supabase.table("logs").insert(row).execute()

def updateLog(log_id, updates: dict):
    supabase.table("logs").update(updates).eq("id", log_id).execute()

def deleteLog(log_id):
    supabase.table("logs").delete().eq("id", log_id).execute()

# ── Exercise ──────────────────────────────────────────────
def getAllExercises():
    return supabase.table("exercises").select("*").execute().data

def appendExercise(row: dict):
    supabase.table("exercises").insert(row).execute()

def updateExercise(program_id, updates: dict):
    supabase.table("exercises").update(updates).eq("id", program_id).execute()

def deleteExercise(program_id):
    supabase.table("exercises").delete().eq("id", program_id).execute()

# ── PROGRAMS ──────────────────────────────────────────────
def getAllPrograms():
    return supabase.table("programs").select("*").execute().data

def appendProgram(row: dict):
    supabase.table("programs").insert(row).execute()

def updateProgram(program_id, updates: dict):
    supabase.table("programs").update(updates).eq("id", program_id).execute()

def deleteProgram(program_id):
    supabase.table("programs").delete().eq("id", program_id).execute()

def renameLogsProgram(user_id, old_program, new_program):
    supabase.table("logs").update({"program": new_program}) \
        .eq("user_id", user_id) \
        .eq("program", old_program) \
        .execute()

# ── feedback ──────────────────────────────────────────────
def getAllFeedback():
    return supabase.table("feedback").select("*").execute().data

def getUserFeedback(user_id):
    data = supabase.table("feedback").select("*").eq("user_id", user_id) \
        .order("message_num", desc=True).order("id", desc=True).limit(1000).execute().data
    return list(reversed(data))

def appendFeedback(row: dict):
    supabase.table("feedback").insert(row).execute()

def updateFeedback(user_id, updates: dict):
    supabase.table("feedback").update(updates).eq("user_id", user_id).execute()