from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify
from datetime import *
import pytz
import bcrypt
import uuid
import random
from db import *

# python liftingTracker/lsdapp.py
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.permanent_session_lifetime = timedelta(days=30)

DATE_FORMATS = {
    0: "%m-%d-%Y", # Month-Day-Year   -> 07-29-2026
    1: "%m/%d/%Y",
    2: "%d-%m-%Y", # Day-Month-Year   -> 29-07-2026
    3: "%d/%m/%Y",
    4: "%Y-%m-%d", # Year-Month-Day   -> 2026-07-29 (same as ISO)
    5: "%Y/%m/%d",
}

def iso_to_display(iso_str: str, fmt: int) -> str:
    d = datetime.strptime(iso_str, "%Y-%m-%d")
    return d.strftime(DATE_FORMATS[int(fmt)])

def display_to_iso(display_str: str, fmt: int) -> str:
    d = datetime.strptime(display_str, DATE_FORMATS[int(fmt)])
    return d.strftime("%Y-%m-%d")

def hashPassword(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def checkPassword(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def isOpen(exercises, order):
    for i in range(len(exercises)):
        if exercises[i]['order'] == order:
            return False
    return True

def calculate_diff(data, program, exercise, set_num, current, max=0):
    for row in reversed(data):
        if (row["program"] == program and
                row["exerciseName"] == exercise and
                int(row["setNum"]) == int(set_num) and max == 0):
            return round(current - float(row["1rm"]), 3)
        elif (row["program"] == program and
                row["exerciseName"] == exercise and
                int(row["setNum"]) == int(set_num) and max == 1):
            return round(current - float(row["weight"]), 3)
    return 0

def get_last_entry(data, program, exercise, set_num, back = 0):
    acc = 0
    for row in reversed(data):
        if row["program"] == program and row["exerciseName"] == exercise:
            if set_num == -1 or int(row["setNum"]) == set_num:
                if acc == back:
                    return row
                acc += 1

    return None

def get_date_entry(data, program, exercise, set_num, date):
    for row in reversed(data):
        if (row["program"] == program and row["exerciseName"] == exercise and
                int(row["setNum"]) == int(set_num) and row["date"] == date):
            return row

    return None

def check_date(date_string, fmt=DATE_FORMATS[1]):
    if not date_string:
        return False
    try:
        datetime.strptime(date_string, fmt)
        return True
    except ValueError:
        return False

def get_best_entry(data, program, exercise, set_num):
    best_1rm = 0

    for row in data:
        if (row["program"] == program and row["exerciseName"] == exercise and
                int(row["setNum"]) == int(set_num)):
            if row["1rm"] > best_1rm:
                best_1rm = row["1rm"]

    return best_1rm

# for each list, regressed, stagnant, progressed, for each exercise, run to check it in this function,
# it will basically check to see if the previous log has a difference positive, negative, or 0. And based on what
# direction is valued at (either being a -1 to represent checking if diff has been regressing, 1 to represent if diff
# has been progressing, and 0 if it has been stagnating) and then count how many occurances of that there are

def get_occurrences(data, program, exercise, set_num, direction=0):
    if direction == 2:
        acc = 1
        for row in reversed(data):
            if row["diff_weight"] == 0:
                acc += 1
            else:
                return acc

    else:
        acc = 0
        for row in reversed(data):
            if (row["program"] == program and row["exerciseName"] == exercise and
                    int(row["setNum"]) == int(set_num)):

                if direction == -1: # if 1rm is regressing
                    if row["diff"] < 0:
                        acc += 1
                    else:
                        return acc
                elif direction == 0: # if 1rm is stagnating
                    if row["diff"] == 0:
                        acc += 1
                    else:
                        return acc
                elif direction == 1: # if 1rm is improving
                    if row["diff"] > 0:
                        acc += 1
                    else:
                        return acc

    return acc

def find_date(data, updated_id, direction=1):
    if direction == 1: # gets the row made after id call
        prev = None
        for row in reversed(data):
            if row["id"] == updated_id:
                return prev
            prev = row
        return None
    else: # gets the row made before id call
        acc = 0
        for row in reversed(data):
            if acc == 1:
                return row
            if row["id"] == updated_id:
                acc += 1
        return None

def generate_report(user_data, exercises, selected, last_entries, prev_entries, newPRs, highlight, highlight_per, heaviest, date_last, date_format, narrator):
    import random

    prd = newPRs
    exercise_names = [ex["exerciseName"] for ex in exercises]

    declined = []
    improved = []
    stagnant = []
    increased = []
    decreased = []

    for ex in exercises:
        key = f"{ex['exerciseName']}_1"
        last = last_entries.get(key)
        prev = prev_entries.get(key)

        if not last or not prev:
            continue

        delta = last["diff"]
        weight_change = last["diff_weight"]
        if delta > 0:
            improved.append(last)
        elif delta < 0:
            declined.append(last)
        else:
            stagnant.append(last)

        if weight_change > 0:
            increased.append(last)
        elif weight_change < 0:
            decreased.append(last)

    total = len(exercise_names)
    numQuality = 1.0 - (len(declined) / total) + (len(improved) / total)
    if numQuality >= .75:
        quality = "excellent"
    elif numQuality >= .5:
        quality = "good"
    elif numQuality >= .25:
        quality = "okay"
    else:
        quality = "poor"

    excellent = ["a marked", "a substantial", "a significant", "a considerable", "a notable"]
    good = ["a clear", "a meaningful", "a visible", "a distinct", "a measurable"]
    okay = ["some", "a moderate", "a partial", "a mild", "a slight"]
    poor = ["a minor", "a marginal", "a negligible", "a barely noticeable", "a trivial"]
    bad = ["an imperceptible", "a questionable", "a dubious", "a supposed", "an alleged"]

    def pick_adj(count, total):
        ratio = count / total
        if ratio >= .8:
            return random.choice(excellent)
        elif ratio >= .6:
            return random.choice(good)
        elif ratio >= .4:
            return random.choice(okay)
        elif ratio >= .2:
            return random.choice(poor)
        else:
            return random.choice(bad)

    def list_exercises(lst):
        if len(lst) == 1:
            return f"{lst[0]['exerciseName']} for {lst[0]['weight']} lbs and {lst[0]['reps']} reps"
        elif len(lst) == 2:
            return (f"{lst[0]['exerciseName']} for {lst[0]['weight']} lbs and {lst[0]['reps']} reps "
                    f"and {lst[1]['exerciseName']} for {lst[1]['weight']} lbs and {lst[1]['reps']} reps")
        else:
            parts = [f"{entry['exerciseName']} for {entry['weight']} lbs and {entry['reps']} reps" for entry in lst]
            return ", ".join(parts[:-1]) + f", and {parts[-1]}" # haha

    reports = []
    report = ""

    # Opening
    pr_ratio = len(prd) / total if total > 0 else 0

    # Overall + highlight + heaviest
    highlight_name = highlight["exerciseName"] if highlight else None
    highlight_weight = highlight["weight"] if highlight else None
    highlight_reps = highlight["reps"] if highlight else None
    heaviest_name = heaviest["exerciseName"] if heaviest else None
    heaviest_weight = heaviest["weight"] if heaviest else None
    heaviest_reps = heaviest["reps"] if heaviest else None

    overall = f"Overall {selected} on {date_last} was {'an' if quality == 'excellent' else 'a'} {quality} {selected} day"
    details = []
    if highlight_name:
        details.append(f"{highlight_name} was the highlight today, improving by {round(highlight_per * 100, 1)}% at {highlight_weight} lbs for {highlight_reps} reps")
    if heaviest_name and heaviest_weight:
        details.append(f"{heaviest_name} was the heaviest exercise at {heaviest_weight} lbs for {heaviest_reps} reps")

    if details:
        overall += ", " + " and ".join(details) + "."
    else:
        overall += "."

    if report:
        connector = " And" if pr_ratio > 0 else " But"
        report += f"{connector} {overall} "
    else:
        report += f"{overall} "
    reports.append(report)

    # Regression
    if declined:
        report = f"There was {pick_adj(len(declined), total)} amount of regression compared to last session, "
        report += f"as {'1 exercise declined' if len(declined) == 1 else f'{len(declined)} exercises declined'} "
        report += f"in the first set out of {total} total — {list_exercises(declined)} {'regressed' if len(declined) > 1 else 'regressed'}."
        streaks = []

        for exercise in declined:
            streak = get_occurrences(user_data, selected, exercise["exerciseName"], 1, -1)

            if streak > 1:
                streaks.append((exercise["exerciseName"], streak))

        if len(streaks) == 1:
            report += f" Worth noting, {streaks[0][0]} has now declined for {streaks[0][1]} straight sessions."
        elif len(streaks) == 2:
            report += (f" Both {streaks[0][0]} and {streaks[1][0]} have been recurring regressors, "
                       f"declining for {streaks[0][1]} and {streaks[1][1]} sessions respectively.")
        elif len(streaks) > 2:
            streak_parts = [f"{ex} ({n} sessions)" for ex, n in streaks]
            joined = ", ".join(streak_parts[:-1]) + f", and {streak_parts[-1]}"
            report += f" Several exercises have been on a declining streak: {joined}."
        reports.append(report)

    # Stagnation
    if stagnant:
        if declined:
            report = "There was also"
        else:
            report = "There was"
        report += f" {pick_adj(len(stagnant), total)} amount of stagnation compared to last session, "
        report += f"as {'1 exercise was' if len(stagnant) == 1 else f'{len(stagnant)} exercises were'} flat "
        report += f"in the first set out of {total} — {list_exercises(stagnant)} didn't move."

        streaks = []
        for exercise in stagnant:
            streak = get_occurrences(user_data, selected, exercise["exerciseName"], 1, 0)
            if streak > 1:
                streaks.append((exercise["exerciseName"], streak))

        if len(streaks) == 1:
            report += f" Worth noting, {streaks[0][0]} has now been stagnant for {streaks[0][1]} straight sessions."
        elif len(streaks) == 2:
            report += (f" Both {streaks[0][0]} and {streaks[1][0]} have been stagnant, "
                       f"being so for {streaks[0][1]} and {streaks[1][1]} sessions respectively.")
        elif len(streaks) > 2:
            streak_parts = [f"{ex} ({n} sessions)" for ex, n in streaks]
            joined = ", ".join(streak_parts[:-1]) + f", and {streak_parts[-1]}"
            report += f" Several exercises have been on a stagnation streak: {joined}."
        reports.append(report)

    # Improvement
    if improved:
        if declined and stagnant:
            report = "However there was"
        elif declined or stagnant:
            report = "But there was also"
        else:
            report = "There was"
        report += f" {pick_adj(len(improved), total)} amount of improvement compared to last session, "
        report += f"as {'1 exercise improved' if len(improved) == 1 else f'{len(improved)} exercises improved'} "
        report += f"in the first set out of {total} — {list_exercises(improved)} improved."

        streaks = []
        for exercise in improved:
            streak = get_occurrences(user_data, selected, exercise["exerciseName"], 1, 1)
            if streak > 1:
                streaks.append((exercise["exerciseName"], streak))

        if len(streaks) == 1:
            report += f" Good work, {streaks[0][0]} has now been improving for {streaks[0][1]} straight sessions."
        elif len(streaks) == 2:
            report += (f" Both {streaks[0][0]} and {streaks[1][0]} have been improving, "
                       f"being so for {streaks[0][1]} and {streaks[1][1]} sessions respectively.")
        elif len(streaks) > 2:
            streak_parts = [f"{ex} ({n} sessions)" for ex, n in streaks]
            joined = ", ".join(streak_parts[:-1]) + f", and {streak_parts[-1]}"
            report += f" Several exercises have been on an improvement streak: {joined}."
        reports.append(report)

    if increased or decreased:
        if declined and stagnant:
            report = "However there was"
        elif declined or stagnant:
            report = "But there was also"
        else:
            report = "There was"

        total_changed = len(increased) + len(decreased)
        report += f" {pick_adj(total_changed, total)} instances of weight change compared to last session, "
        report += f"as {'1 exercise changed' if total_changed == 1 else f'{total_changed} exercises changed'} "
        report += f"in the first set out of {total}"

        if increased and decreased:
            report += f" — {list_exercises(increased)} increased in weight and {list_exercises(decreased)} decreased in weight."
        elif increased:
            report += f" — {list_exercises(increased)} increased in weight."
        else:
            report += f" — {list_exercises(decreased)} decreased in weight."

        dni = []
        ind = []

        for exercise in increased:
            if exercise in declined:
                ind.append(exercise)

        for exercise in decreased:
            if exercise in improved:
                dni.append(exercise)

        if ind:
            report += (f" Do note that out of the exercises that declined in 1RM values, {list_exercises(declined)}, "
                       f"{len(ind)} of them also increased in weight — {list_exercises(ind)}, which you may wish to dismiss.")

        if dni:
            report += (f" Do note that out of the exercises that improved in 1RM values, {list_exercises(improved)}, "
                       f"{len(dni)} of them also decreased in weight — {list_exercises(dni)}, which you may wish to dismiss.")

        streaks = []
        for exercise in improved:
            streak = get_occurrences(user_data, selected, exercise["exerciseName"], 1, 1)
            if streak > 1:
                streaks.append((exercise["exerciseName"], streak))

        if len(streaks) == 1:
            report += f" Good work, {streaks[0][0]} has now been improving for {streaks[0][1]} straight sessions."
        elif len(streaks) == 2:
            report += (f" Both {streaks[0][0]} and {streaks[1][0]} have been improving, "
                       f"being so for {streaks[0][1]} and {streaks[1][1]} sessions respectively.")
        elif len(streaks) > 2:
            streak_parts = [f"{ex} ({n} sessions)" for ex, n in streaks]
            joined = ", ".join(streak_parts[:-1]) + f", and {streak_parts[-1]}"
            report += f" Several exercises have been on an improvement streak: {joined}."
        reports.append(report)

    # Notes
    notes = []
    for ex in exercises:
        for s in range(1, int(ex["numSets"]) + 1):
            key = f"{ex['exerciseName']}_{s}"
            last = last_entries.get(key)
            if last and last["notes"] != "":
                notes.append(last)

    if notes:
        report = " Some notes were made this session —"
        for i, entry in enumerate(notes):
            note_text = f" on {entry['exerciseName']} where you lifted {entry['weight']} lbs for {entry['reps']} reps, you wrote \"{entry['notes']}\""
            if i < len(notes) - 1:
                report += note_text + ","
            else:
                report += note_text + "."
        reports.append(report)

    # Closing



    return reports

def parseRepRange(repRange, numSets):
    try:
        parts = [int(x.strip()) for x in str(repRange).split(",")]

        if len(parts) >= numSets:
            return parts[:numSets]
        else:
            return parts + [parts[-1]] * (numSets - len(parts))
    except ValueError:
        return []

def getLastEnteredLog(user_id, program=None):
    query = supabase.table("Logs").select("*").eq("userId", user_id)
    if program:
        query = query.eq("program", program)
    data = query.order("id", desc=True).limit(1).execute().data
    return data[0] if data else None

@app.route("/", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    error = None
    if request.method == "POST":
        action = request.form.get("action")
        users = getAllUsers()

        if action == "login":
            username = request.form.get("username")
            password = request.form.get("password")
            user = next((u for u in users if u["username"] == username), None)
            if user and checkPassword(password, user["password"]):
                session.permanent = True
                session["user_id"] = user["userId"]
                session["username"] = user["username"]
                session["settings"] = {
                    "narrator": user.get("narrator", "default"),
                    "quick_indexing": bool(int(user.get("quick_indexing", 1))),
                }
                return redirect(url_for("home"))
            else:
                error = "Invalid username or password."

        elif action == "register":
            new_username = request.form.get("new_username")
            new_password = request.form.get("new_password")
            confirm = request.form.get("confirm_password")
            if not new_username or not new_password:
                error = "Please fill in all fields."
            elif new_password != confirm:
                error = "Passwords don't match."
            elif any(u["username"] == new_username for u in users):
                error = "Username already taken."
            else:
                new_id = getNextUserId()
                appendUser({
                    "username": new_username,
                    "password": hashPassword(new_password),
                    "userId": new_id,
                    "narrator": "default",
                    "quick_indexing": 1,
                    "quick_resume": 1,
                    "date_format": 1,
                    "show_rep": 1,
                    "show_last": 1,
                    "show_streak": 1,
                    "show_rec": 1,
                    "weight_autofill": 1,
                    "reps_autofill": 1,
                    "weight_autofill_absent": 1,
                    "reps_autofill_absent": 1
                })
                error = "Account created! You can now log in."

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST" and request.form.get("action") == "save_settings":
        narrator = request.form.get("narrator", "default")
        show_rep = 1 if request.form.get("show_rep") else 0
        show_last = 1 if request.form.get("show_last") else 0
        show_streak = 1 if request.form.get("show_streak") else 0
        show_rec = 1 if request.form.get("show_rec") else 0
        quick_indexing = 1 if request.form.get("quick_indexing") else 0
        quick_resume = 1 if request.form.get("quick_resume") else 0
        date_format = request.form.get("date_format", 1)
        weight_autofill = request.form.get("weight_autofill", 1)
        reps_autofill = request.form.get("reps_autofill", 1)
        weight_autofill_absent = request.form.get("weight_autofill_absent", 1)
        reps_autofill_absent = request.form.get("reps_autofill_absent", 1)

        updateUser(session["user_id"], {
            "narrator": narrator,
            "quick_indexing": quick_indexing,
            "quick_resume": quick_resume,
            "date_format": date_format,
            "show_rep": show_rep,
            "show_last": show_last,
            "show_streak": show_streak,
            "show_rec": show_rec,
            "weight_autofill": int(weight_autofill),
            "reps_autofill": int(reps_autofill),
            "weight_autofill_absent": int(weight_autofill_absent),
            "reps_autofill_absent": int(reps_autofill_absent)
        })

        session["settings"] = {
            "narrator": narrator,
            "quick_indexing": quick_indexing,
            "quick_resume": quick_resume,
            "date_format": date_format,
            "show_rep": show_rep,
            "show_last": show_last,
            "show_streak": show_streak,
            "show_rec": show_rec,
            "weight_autofill": int(weight_autofill),
            "reps_autofill": int(reps_autofill),
            "weight_autofill_absent": int(weight_autofill_absent),
            "reps_autofill_absent": int(reps_autofill_absent)
        }

        return redirect(url_for("settings", success=1))

    success_message = "Settings saved!" if request.args.get("success") else None

    users = getAllUsers()
    user = next((u for u in users if str(u["userId"]) == str(session["user_id"])), None)

    settings = {
        "narrator": user.get("narrator", "default") if user else "default",
        "quick_indexing": bool(int(user.get("quick_indexing", 1))) if user else True,
        "quick_resume": bool(int(user.get("quick_resume", 1))) if user else True,
        "date_format": user.get("date_format", 1) if user else 1,
        "show_rep": bool(int(user.get("show_rep", 1))) if user else True,
        "show_last": bool(int(user.get("show_last", 1))) if user else True,
        "show_streak": bool(int(user.get("show_streak", 1))) if user else True,
        "show_rec": bool(int(user.get("show_rec", 1))) if user else True,
        "weight_autofill": user.get("weight_autofill", 1) if user else 1,
        "reps_autofill": user.get("reps_autofill", 1) if user else 1,
        "weight_autofill_absent": user.get("weight_autofill_absent", 1) if user else 1,
        "reps_autofill_absent": user.get("reps_autofill_absent", 1) if user else 1
    }

    return render_template("settings.html", settings=settings, success_message=success_message)

@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    prog_data = getAllProgram()
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    user_data = getUserLogs(session["user_id"])
    num_prog = len(set(row["programName"] for row in user_prog))
    my_programs = []

    for row in reversed(user_data):
        if row["program"] not in my_programs:
            my_programs.append(row["program"])
        if len(my_programs) == num_prog:
            break

    my_programs.reverse()

    # print(my_programs)
    # my_programs = my_programs.reverse()

    log_cap_warning = len(user_data) >= 1000
    #print(f"Total logs fetched: {len(getAllLogs())}, User logs: {len(user_data)}")
    forced_home = request.args.get("home") == "1"

    narrator = session.get("settings", {}).get("narrator", "default")
    if narrator == "mommy":
        welcome_message = f"Mommy is so happy to see you again!"
    elif narrator == "hard":
        welcome_message = f"Surprised to see you here again fatso."
    elif narrator == "goth":
        welcome_message = f"Look who came back for more."
    elif narrator == "mort":
        welcome_message = f"ALL HAIL KING JULIEN!"
    else:
        welcome_message = f"Welcome back {session['username']}"

    last = user_data[-1] if user_data else None
    last_exercise_in_program = sorted(
        [row for row in user_prog if row["programName"] == last["program"]],
        key=lambda x: int(x["order"])
    )[-1] if last else None

    workout_incomplete = last and (
            (last["exerciseName"] != last_exercise_in_program["exerciseName"]) or
            (last["setNum"] != last_exercise_in_program["numSets"])
    )
    quick_resume = session.get("settings", {}).get("quick_resume", 1)

    if workout_incomplete and not forced_home and quick_resume == 1:
        return redirect(url_for("run"))
    date = iso_to_display(last["date"], session.get("settings", {}).get("date_format", 1)) if last else None

    return render_template("home.html",
                           username=session["username"],
                           user_prog=user_prog,
                           my_programs=my_programs,
                           user_data=user_data,
                           log_cap_warning=log_cap_warning,
                           welcome_message=welcome_message,
                           date=date
                           )

@app.route("/run", methods=["GET", "POST"])
def run():
    if "user_id" not in session:
        return redirect(url_for("login"))

    prog_data = getAllProgram()
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog if row["programName"] != " "))

    user_data = getUserLogs(session["user_id"])
    log_cap_warning = len(user_data) >= 1000

    if not my_programs:
        return render_template("run.html", my_programs=[], exercises=[], user_data=[],
                               selected=None, today="")

    selected = request.args.get("program") or request.form.get("selected_program")
    if not selected or selected not in my_programs:
        last_program = user_data[-1]["program"] if user_data else None
        selected = last_program if last_program in my_programs else my_programs[0]

    exercises = sorted(
        [row for row in user_prog if row["programName"] == selected],
        key=lambda x: int(x["order"])
    )

    timezone = pytz.timezone("America/Chicago")
    now = datetime.now(timezone)
    today = now.strftime("%Y-%m-%d")
    success_message = None
    error_message = ""

    ex_index = request.args.get("ex_index", type=int)

    if ex_index is None:
        programLogs = [row for row in user_data if row["program"] == selected]
        last = programLogs[-1] if programLogs else None

        if last and (today == last["date"]):
            last_ex = last["exerciseName"]
            match = next((e for e in exercises if e["exerciseName"] == last_ex), None)
            if match:
                current_index = int(match["order"]) - 1
                if int(last["setNum"]) >= int(match["numSets"]):
                    if int(match["order"]) == int(exercises[-1]["order"]):
                        ex_index = 0
                    else:
                        ex_index = current_index + 1
                else:
                    ex_index = current_index
            else:
                ex_index = 0
        else:
            ex_index = 0

    if request.method == "POST" and request.form.get("action") == "log_set":
        workout_date = request.form.get("workout_date")

        if not check_date(workout_date):
            date_format = session.get('settings', {}).get('date_format', 1)
            error_message = (f"Invalid date format! Please use MM-DD-YYYY (e.g., "
                             f"{iso_to_display(today, date_format)}).")
        else:
            exercise_name = request.form.get("exercise_name")
            set_num = int(request.form.get("set_num"))
            weight = float(request.form.get("weight"))
            reps = int(request.form.get("reps"))
            notes = request.form.get("notes", "")
            selected = request.form.get("selected_program")

            one_rm = round(weight * (1 + float(reps) / 30), 3)
            diff = calculate_diff(user_data, selected, exercise_name, set_num, one_rm)
            diff_weight = calculate_diff(user_data, selected, exercise_name, set_num, weight, 1)

            appendLog({
                "userId": int(session["user_id"]),
                "program": selected,
                "status": 1,
                "date": display_to_iso(workout_date, 1),
                "exerciseName": exercise_name,
                "setNum": set_num,
                "weight": weight,
                "reps": reps,
                "1rm": one_rm,
                "diff": diff,
                "notes": notes,
                "diff_weight": diff_weight
            })

            user_data = getUserLogs(session["user_id"])

            narrator = session.get("settings", {}).get("narrator", "default")
            if narrator == "mommy":
                success_message = f"Good job sweetie! Set {set_num} logged — 1RM: {one_rm} | Diff: {diff} — Weight: {weight} | Diff: {diff_weight}"
            elif narrator == "hard":
                success_message = f"Alright I wrote that down, but don't get your hopes up. Set {set_num} logged — 1RM: {one_rm} | Diff: {diff} — Weight: {weight} | Diff: {diff_weight}"
            elif narrator == "goth":
                success_message = f"You like this, don't you baby? Set {set_num} logged — 1RM: {one_rm} | Diff: {diff} — Weight: {weight} | Diff: {diff_weight}"
            elif narrator == "mort":
                success_message = f"Yay! I love you King King Julien. Set {set_num} logged — 1RM: {one_rm} | Diff: {diff} — Weight: {weight} | Diff: {diff_weight}"
            else:
                success_message = f"Logged {exercise_name} Set {set_num} — 1RM: {one_rm} | Diff: {diff} — Weight: {weight} | Diff: {diff_weight}"

            exercises = sorted(
                [row for row in user_prog if row["programName"] == selected],
                key=lambda x: int(x["order"])
            )

            quick_index = session.get("settings", {}).get("quick_indexing", 1)
            match = next((e for e in exercises if e["exerciseName"] == exercise_name), None)
            if quick_index == 1:
                if match:
                    current_index = int(match["order"]) - 1
                    if set_num >= int(match["numSets"]):
                        if int(match["order"]) == int(exercises[-1]["order"]):
                            ex_index = current_index
                        else:
                            ex_index = current_index + 1
                    else:
                        ex_index = current_index
                else:
                    ex_index = 0

    ex_index = max(0, min(ex_index, len(exercises) - 1))

    rep_ranges = {}
    last_entries = {}
    recommendations = {}
    streaks_1rm = {}
    streaks_weight = {}
    rec_weights = {}
    rec_reps = {}
    for ex in exercises:
        minRepRange = [int(x.strip()) for x in str(ex["minReps"]).split(",")]
        maxRepRange = [int(x.strip()) for x in str(ex["maxReps"]).split(",")]

        for s in range(1, int(ex["numSets"]) + 1):
            key = f"{ex['exerciseName']}_{s}"
            date_format = session.get("settings", {}).get("date_format", 1)
            last_entries[key] = get_last_entry(user_data, selected, ex["exerciseName"], s)
            last_entries[key]["date"] = iso_to_display(last_entries[key]["date"], date_format)
            last = last_entries[key]

            # units[key] = ex["unit"]

            if (maxRepRange[s-1] == 0) or (session.get("settings", {}).get("show_rep", 1) == 0):
                rep_ranges[key] = None
            elif minRepRange[s-1] == maxRepRange[s-1]:
                rep_ranges[key] = f"Target for set {s} is {minRepRange[s-1]} {ex['unit']}s."
            else:
                rep_ranges[key] = f"Range for set {s} is {minRepRange[s-1]}-{maxRepRange[s-1]} {ex['unit']}s." # here

            if last:
                if last["diff"] > 0:
                    streak_1rm = 1
                elif last["diff"] < 0:
                    streak_1rm = -1
                else:
                    streak_1rm = 0

                occur_1rm = get_occurrences(user_data, selected, ex["exerciseName"], s, streak_1rm)
                occur_weight = get_occurrences(user_data, selected, ex["exerciseName"], s, 2)

                if occur_1rm and (session.get("settings", {}).get("show_streak", 1) == 1):
                    streak_1rm_message = f"1RM Streak: {occur_1rm} session "
                    if streak_1rm == -1:
                        streak_1rm_message += f"regression streak."
                    elif streak_1rm == 0:
                        streak_1rm_message += f"stagnation streak."
                    elif streak_1rm == 1:
                        streak_1rm_message += f"improvement streak."
                    streaks_1rm[key] = streak_1rm_message

                if occur_weight and (session.get("settings", {}).get("show_streak", 1) == 1):
                    streaks_weight[key] = f"Weight Streak: {last_entries[key]["weight"]} lbs for {occur_weight} {'sessions' if occur_weight != 1 else 'session'}."

                if (maxRepRange[s - 1] == 0) or (session.get("settings", {}).get("show_rec", 1) == 0):
                    recommendations[key] = None
                elif int(last["reps"]) >= int(maxRepRange[s-1] * 1.25):
                    # if last reps are significantly more than max or significantly less than min
                    rec_weight = round((last["1rm"] / (1 + (minRepRange[s-1] / 30))) / ex["increment"]) * ex["increment"]
                    recommendations[key] = f"Recommended: {rec_weight} lbs for {minRepRange[s-1]} {ex['unit']}s"
                    rec_weights[key] = float(rec_weight)
                    rec_reps[key] = int(minRepRange[s-1])
                elif int(last["reps"]) < int((minRepRange[s-1] - 1) * .75):
                    rec_weight = round((last["1rm"] / (1 + (maxRepRange[s-1] / 30))) / ex["increment"]) * ex["increment"]
                    recommendations[key] = f"Recommended: {rec_weight} lbs for {maxRepRange[s-1]} {ex['unit']}s"
                    rec_weights[key] = float(rec_weight)
                    rec_reps[key] = int(maxRepRange[s-1])
                elif int(last["reps"]) >= maxRepRange[s-1]: # if last reps are more than max
                    rec_weight = float(last["weight"]) + float(ex["increment"])
                    recommendations[key] = f"Recommended: {rec_weight} lbs for {minRepRange[s-1]} {ex['unit']}s"
                    rec_weights[key] = float(rec_weight)
                    rec_reps[key] = int(minRepRange[s-1])
                elif int(last["reps"]) < minRepRange[s-1] - 1: # if last reps are less than min
                    rec_weight = float(last["weight"]) - float(ex["increment"])
                    recommendations[key] = f"Recommended: {rec_weight} lbs for {maxRepRange[s-1]} {ex['unit']}s"
                    rec_weights[key] = float(rec_weight)
                    rec_reps[key] = int(maxRepRange[s-1])
                else: # if last reps are between max and min
                    recommendations[key] = f"Recommended: {last['weight']} lbs for {int(last['reps']) + 1} {ex['unit']}s"
                    rec_weights[key] = float(last['weight'])
                    rec_reps[key] = int(last['reps']) + 1

    prev_entries = {}
    for ex in exercises:
        key = f"{ex['exerciseName']}"
        prev_entries[key] = get_last_entry(user_data, selected, ex["exerciseName"], -1)

    # print(f"rec_weights: {rec_weights}")
    # print(f"rec_reps: {rec_reps}")
    formated_date = iso_to_display(today, session.get('settings', {}).get('date_format', 1))
    response = make_response(render_template("run.html",
                                             my_programs=my_programs, # program data (data)
                                             selected=selected, # selected exercise (string)
                                             exercises=exercises,# list of exercises (data)
                                             ex_index=ex_index, # what exercise the user is on
                                             today=formated_date, # date
                                             last_entries=last_entries, # data from previous session
                                             prev_entries=prev_entries, # for last log only
                                             recommendations=recommendations, # recommendations (dict of strings)
                                             streaks_1rm=streaks_1rm, # streaks (dict of strings)
                                             streaks_weight=streaks_weight,
                                             rep_ranges=rep_ranges, # rep ranges for the sets (dict of strings)
                                             rec_weights=rec_weights, # recommended weight (dict of floats)
                                             rec_reps=rec_reps, # recommended rep amounts (dict of ints)
                                             user_data=user_data, # user logs (data)
                                             log_cap_warning=log_cap_warning,
                                             error_message=error_message,
                                             success_message=success_message,
                                             show_last=session.get("settings", {}).get("show_last", 1),
                                             weight_autofill=session.get("settings", {}).get("weight_autofill", 1),
                                             reps_autofill=session.get("settings", {}).get("reps_autofill", 1),
                                             weight_autofill_absent=session.get("settings", {}).get(
                                                 "weight_autofill_absent", 1),
                                             reps_autofill_absent=session.get("settings", {}).get(
                                                 "reps_autofill_absent", 1)
                                             ))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/run/results")
def run_results():
    if "user_id" not in session:
        return redirect(url_for("login"))

    prog_data = getAllProgram()
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog if row["programName"] != " "))
    date_format = session.get("settings", {}).get("date_format", 1)

    user_data = getUserLogs(session["user_id"])

    selected = request.args.get("program")
    if not selected or selected not in my_programs:
        selected = user_data[-1]["program"] if user_data else None
    if not selected:
        return redirect(url_for("run"))

    exercises = sorted(
        [row for row in user_prog if row["programName"] == selected],
        key=lambda x: int(x["order"])
    )

    # Get all unique dates for this program, sorted newest first
    program_dates = sorted(
        list(set(row["date"] for row in user_data if row["program"] == selected)),
        reverse=True
    )

    if not program_dates or not exercises:
        return render_template("results.html",
                               selected=selected,
                               my_programs=my_programs,
                               exercises=exercises,
                               last_entries={},
                               prev_entries={},
                               highlight=None,
                               heaviest=None,
                               newPRs=[],
                               report=None,
                               program_dates=[],
                               date_last=None,
                               date_prev=None,
                               narrator=session.get("settings", {}).get("narrator", "default"))

    timezone = pytz.timezone("America/Chicago")
    # now = datetime.now(timezone)
    # today = now.strftime(date_format)

    # Default: two most recent dates
    date_last = request.args.get("date_last", program_dates[0] if len(program_dates) > 0 else None)
    date_prev = request.args.get("date_prev", program_dates[1] if len(program_dates) > 1 else None)

    user_data = getUserLogsByDates(session["user_id"], selected, date_last, date_prev)

    last_entries = {}
    prev_entries = {}
    currentImprov = 0
    currentHvy = 0
    highlight = None
    heaviest = None
    newPRs = []

    for ex in exercises:
        for s in range(1, int(ex["numSets"]) + 1):
            key = f"{ex['exerciseName']}_{s}"

            last = get_date_entry(user_data, selected, ex["exerciseName"], s, date_last) if date_last else None
            prev = get_date_entry(user_data, selected, ex["exerciseName"], s, date_prev) if date_prev else None

            last_entries[key] = last
            # last_entries[key]["date"] = iso_to_display(last_entries[key]["date"], date_format)
            prev_entries[key] = prev
            # prev_entries[key]["date"] = iso_to_display(prev_entries[key]["date"], date_format)

            if not last or not prev:
                continue

            newImprov = 1.0 - (prev["1rm"] / last["1rm"])
            newHvy = last["weight"]
            if newImprov > currentImprov:
                currentImprov = newImprov
                highlight = last

            if newHvy > currentHvy:
                currentHvy = newHvy
                heaviest = last

            if s == 1:
                all_time_best = get_best_entry(user_data, selected, ex['exerciseName'], 1)
                if last["1rm"] >= all_time_best:
                    newPRs.append(ex['exerciseName'])
    narrator = session.get("settings", {}).get("narrator", "default")
    date_format = session.get("settings", {}).get("date_format", 1)
    date_last_visual, date_prev_visual = iso_to_display(date_last, date_format), iso_to_display(date_prev, date_format)
    report = generate_report(user_data, exercises, selected, last_entries, prev_entries, newPRs, highlight,
                             currentImprov, heaviest, date_last_visual, date_format, narrator)

    program_dates_display = {d: iso_to_display(d, date_format) for d in program_dates}

    return render_template("results.html",
                           selected=selected,
                           my_programs=my_programs,
                           exercises=exercises,
                           last_entries=last_entries,
                           prev_entries=prev_entries,
                           highlight=highlight,
                           heaviest=heaviest,
                           newPRs=newPRs,
                           report=report,
                           program_dates=program_dates,
                           program_dates_display=program_dates_display,
                           date_last=date_last,
                           date_last_visual=date_last_visual,
                           date_prev=date_prev,
                           date_prev_visual=date_prev_visual,
                           narrator=narrator)


@app.route("/manage", methods=["GET", "POST"])
def manage():
    if "user_id" not in session:
        return redirect(url_for("login"))

    prog_data = getAllProgram()
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog))
    user_data = getUserLogs(session["user_id"])
    log_cap_warning = len(user_data) >= 1000

    max_exercises = 25
    success_message = None
    error_message = None

    if request.method == "POST":
        selected_edit = request.form.get("selected_program") or request.args.get("program")
    else:
        selected_edit = request.args.get("program")

    # Keep your fallback logic right below it
    if not selected_edit or selected_edit not in my_programs:
        selected_edit = my_programs[0] if my_programs else None

    action = request.form.get("action")

    if request.method == "POST":
        if action == "create_program":
            new_program_name = request.form.get("new_program_name", "").strip()
            if not new_program_name:
                error_message = "Please enter a program name."
            elif new_program_name in my_programs:
                error_message = "A program with that name already exists."
            else:
                appendProgram({
                    "userId": int(session["user_id"]),
                    "programName": new_program_name,
                    "exerciseName": "",
                    "numSets": 0,
                    "increment": 0,
                    "minReps": "0",
                    "maxReps": "0",
                    "order": 0,
                    "notes": "",
                    "unit": "rep"
                })
                my_programs.append(new_program_name)
                selected_edit = new_program_name
                success_message = f"Program '{new_program_name}' created! Now add exercises to it."

        elif action == "delete_program":
            # Delete all program rows
            rows_to_delete = [row for row in user_prog
                              if str(row["userId"]) == str(session["user_id"])
                              and row["programName"] == selected_edit]
            for row in rows_to_delete:
                deleteProgram(row["id"])

            # Set status to 0 in logs
            logs_to_update = [row for row in user_data
                              if row["program"] == selected_edit]
            for row in logs_to_update:
                updateLog(row["id"], {"status": 0})

            success_message = f"Deleted program '{selected_edit}'!"
            my_programs = [p for p in my_programs if p != selected_edit]
            selected_edit = my_programs[0] if my_programs else None
            prog_data = getAllProgram()
            user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]

        elif action == "add_exercise":
            new_exercise = request.form.get("new_exercise", "").strip()
            new_sets = int(request.form.get("new_sets", 1))
            new_inc = float(request.form.get("new_inc", 5.0))
            new_min = request.form.get("new_min", "6,2")
            new_max = request.form.get("new_max", "8,4")
            new_notes = request.form.get("new_notes", "")
            new_order = int(request.form.get("new_order", 1))
            new_unit = request.form.get("new_unit", "rep")
            edit_exercises = [row for row in user_prog if row["programName"] == selected_edit]

            new_min = parseRepRange(new_min, new_sets)
            new_max = parseRepRange(new_max, new_sets)
            rangeError = False


            if len(new_min) != 0 and len(new_max) != 0:
                for i in range(len(new_min)):
                    if new_min[i] > new_max[i]:
                        rangeError = True
                        break

            if not new_exercise:
                error_message = "Please enter an exercise name."
            elif len(new_min) == 0 or len(new_max) == 0:
                error_message = "Please enter a valid range."
            elif rangeError:
                error_message = "Minimum units must be less than or equal to maximum units."
            else:
                # Handle order conflict
                for ex in edit_exercises:
                    if int(ex["order"]) == new_order:
                        next_order = max(int(e["order"]) for e in edit_exercises) + 1
                        updateProgram(ex["id"], {"order": next_order})
                        break

                # Remove placeholder row if exists
                placeholder = next((row for row in edit_exercises
                                    if not str(row["exerciseName"]).strip()), None)
                if placeholder:
                    deleteProgram(placeholder["id"])

                appendProgram({
                    "userId": int(session["user_id"]),
                    "programName": selected_edit,
                    "exerciseName": new_exercise,
                    "numSets": new_sets,
                    "increment": new_inc,
                    "minReps": ",".join(str(x) for x in new_min),
                    "maxReps": ",".join(str(x) for x in new_max),
                    "order": new_order,
                    "notes": new_notes,
                    "unit": new_unit
                })

                # check for deleted logs, if any exist, set their status to alive again
                logs_to_update = [row for row in user_data
                                  if row["program"] == selected_edit
                                  and row["exerciseName"] == new_exercise
                                  and int(row["status"]) == 0]  # only dead logs
                for row in logs_to_update:
                    updateLog(row["id"], {"status": 1})

                success_message = f"Added {new_exercise} to {selected_edit}!"
                prog_data = getAllProgram()
                user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]

        elif action == "delete_exercise":
            exercise_name = request.form.get("exercise_name")
            edit_exercises = [row for row in user_prog if row["programName"] == selected_edit]

            deleted_order = next((int(row["order"]) for row in edit_exercises
                                  if row["exerciseName"] == exercise_name), None)

            # Delete the exercise
            for row in edit_exercises:
                if row["exerciseName"] == exercise_name:
                    deleteProgram(row["id"])

            # Shift order down for exercises that followed
            if deleted_order is not None:
                for row in edit_exercises:
                    if int(row["order"]) > deleted_order:
                        updateProgram(row["id"], {"order": int(row["order"]) - 1})

            # Set status to 0 in logs
            logs_to_update = [row for row in user_data
                              if row["program"] == selected_edit
                              and row["exerciseName"] == exercise_name]
            for row in logs_to_update:
                updateLog(row["id"], {"status": 0})

            success_message = f"Deleted {exercise_name}!"
            prog_data = getAllProgram()
            user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]

        elif action == "save_exercise":
            exercise_name = request.form.get("exercise_name")
            upd_name = request.form.get("upd_name", exercise_name).strip()
            upd_sets = int(request.form.get("upd_sets"))
            upd_inc = float(request.form.get("upd_inc"))
            upd_min = request.form.get("upd_min")
            upd_max = request.form.get("upd_max")
            upd_notes = request.form.get("upd_notes", "")
            upd_order = int(request.form.get("upd_order"))
            upd_unit = request.form.get("upd_unit")
            edit_exercises = [row for row in user_prog if row["programName"] == selected_edit]

            upd_min = parseRepRange(upd_min, upd_sets)
            upd_max = parseRepRange(upd_max, upd_sets)
            rangeError = False

            if len(upd_min) != 0 and len(upd_max) != 0:
                for i in range(len(upd_min)):
                    if upd_min[i] > upd_max[i]:
                        rangeError = True
                        break

            if not exercise_name:
                error_message = "Please enter an exercise name."
            elif len(upd_min) == 0 or len(upd_max) == 0:
                error_message = "Please enter a valid range."
            elif rangeError:
                error_message = "Minimum units must be less than or equal to maximum units."
            else:
                # Handle order conflict
                swapped_name = None
                for ex in edit_exercises:
                    if int(ex["order"]) == upd_order and ex["exerciseName"] != exercise_name:
                        swapped_name = ex["exerciseName"]
                        orig_order = next(e["order"] for e in edit_exercises if e["exerciseName"] == exercise_name)
                        updateProgram(ex["id"], {"order": int(orig_order)})
                        break

                # Update the exercise
                target = next((row for row in edit_exercises if row["exerciseName"] == exercise_name), None)
                if target:
                    updateProgram(target["id"], {
                        "exerciseName": upd_name,
                        "numSets": upd_sets,
                        "increment": upd_inc,
                        "minReps": ",".join(str(x) for x in upd_min),
                        "maxReps": ",".join(str(x) for x in upd_max),
                        "order": upd_order,
                        "notes": upd_notes,
                        "unit": upd_unit
                    })

                # Rename in logs if name changed
                if upd_name != exercise_name:
                    logs_to_update = [row for row in user_data
                                      if row["program"] == selected_edit
                                      and row["exerciseName"] == exercise_name]
                    for row in logs_to_update:
                        updateLog(row["id"], {"exerciseName": upd_name})

                    # check for deleted logs, if any exist, set their status to alive again
                    logs_to_update = [row for row in user_data
                                      if row["program"] == selected_edit
                                      and row["exerciseName"] == upd_name  # use upd_name, not exercise_name
                                      and int(row["status"]) == 0]
                    for row in logs_to_update:
                        updateLog(row["id"], {"status": 1})

                success_message = f"Saved changes to {upd_name}!"
                if swapped_name:
                    success_message += f" Swapped order with '{swapped_name}'."
                prog_data = getAllProgram()
                user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]

    edit_exercises = sorted(
        [row for row in user_prog if row["programName"] == selected_edit and row["exerciseName"] != ""],
        key=lambda x: int(x["order"])
    ) if selected_edit else []

    next_order = (max(int(e["order"]) for e in edit_exercises) + 1) if edit_exercises else 1

    return render_template("manage.html",
                           my_programs=my_programs,
                           selected_edit=selected_edit,
                           edit_exercises=edit_exercises,
                           next_order=next_order,
                           max_exercises=max_exercises,
                           log_cap_warning=log_cap_warning,
                           success_message=success_message,
                           error_message=error_message)

@app.route("/templates", methods=["GET", "POST"])
def templates():
    if "user_id" not in session:
        return redirect(url_for("login"))

    prog_data = getAllProgram()
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog if row["programName"] != " "))

    template_prog = [row for row in prog_data if str(row["userId"]) == str(TEMPLATE_USER_ID) and row["exerciseName"] != ""]
    template_programs = list(set(row["programName"] for row in template_prog))

    success_message = None
    error_message = None

    if request.method == "POST" and request.form.get("action") == "copy_program":
        prog_name = request.form.get("program_name")

        if prog_name in my_programs:
            error_message = f"You already have a program called '{prog_name}'."
        else:
            rows_to_copy = [row for row in template_prog if row["programName"] == prog_name]
            for row in rows_to_copy:
                appendProgram({
                    "userId": int(session["user_id"]),
                    "programName": row["programName"],
                    "exerciseName": row["exerciseName"],
                    "numSets": row["numSets"],
                    "increment": row["increment"],
                    "minReps": row["minReps"],
                    "maxReps": row["maxReps"],
                    "order": row["order"],
                    "notes": row["notes"]
                })
            success_message = f"'{prog_name}' added to your programs!"
            my_programs.append(prog_name)

    return render_template("templates.html",
                           template_prog=template_prog,
                           template_programs=sorted(template_programs),
                           my_programs=my_programs,
                           success_message=success_message,
                           error_message=error_message)

@app.route("/logs", methods=["GET", "POST"])
def logs():
    if "user_id" not in session:
        return redirect(url_for("login"))

    prog_data = getAllProgram() # all the programs
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])] # only the users programs
    my_programs = list(set(row["programName"] for row in user_prog)) # list of the names of the users programs
    date_format = session.get("settings", {}).get("date_format", 1)
    last_overall = getLastEnteredLog(session["user_id"])

    success_message = None
    error_message = None

    selected_prog = request.args.get("program") or request.form.get("selected_prog")# selected prog
    if not selected_prog or selected_prog not in my_programs:
        if last_overall:
            selected_prog = last_overall["program"]
        else:
            selected_prog = my_programs[0] if my_programs else None

    selected_ex = request.args.get("exercise") or request.form.get("selected_ex")
    exercises = [row for row in user_prog if row["programName"] == selected_prog]
    exercise_names = [row["exerciseName"] for row in exercises]
    if not selected_ex or selected_ex not in exercise_names:
        last_in_prog = getLastEnteredLog(session["user_id"], program=selected_prog)
        if last_in_prog:
            selected_ex = last_in_prog["exerciseName"]
        else:
            selected_ex = exercise_names[0] if exercise_names else None

    exercise_data = next((row for row in exercises if row["exerciseName"] == selected_ex), None)
    num_sets = int(exercise_data["numSets"]) if exercise_data else 1
    selected_unit  = exercise_data["unit"] if exercise_data else "rep"
    #print(selected_unit)

    selected_set = int(request.args.get("set_num") or request.form.get("selected_set") or 1)
    if selected_set < 1:
        selected_set = 1
    if selected_set > num_sets:
        selected_set = num_sets

    user_data_exercise = getUserLogsByExercise(session["user_id"], selected_prog, selected_ex, selected_set)

    programLogs = [row for row in user_data_exercise]
    last = programLogs[-1] if programLogs else None

    action = request.form.get("action")
    # unit = exercises[selected_ex]["unit"]

    if request.method == "POST":
        if action == "delete_log":
            log_date = display_to_iso(request.form.get("log_date"), date_format)
            log_weight = request.form.get("log_weight")
            log_reps = request.form.get("log_reps")
            log_notes = request.form.get("log_notes")

            matching = [row for row in user_data_exercise
                        if str(row["userId"]) == str(session["user_id"]) and
                        row["program"] == selected_prog and
                        row["exerciseName"] == selected_ex and
                        int(row["setNum"]) == selected_set and
                        row["date"] == log_date and
                        float(row["weight"]) == float(log_weight) and
                        int(row["reps"]) == int(log_reps) and
                        str(row["notes"]) == str(log_notes)]
            for row in matching:
                deleteLog(row["id"])
            success_message = "Log deleted!"
            user_data_exercise = getUserLogs(session["user_id"])


        elif action == "save_log":
            orig_date = display_to_iso(request.form.get("orig_date"), date_format)
            orig_weight = request.form.get("orig_weight")
            orig_reps = request.form.get("orig_reps")
            orig_notes = request.form.get("orig_notes")
            upd_date = display_to_iso(request.form.get("upd_date"), date_format)
            upd_weight = float(request.form.get("upd_weight"))
            upd_reps = int(request.form.get("upd_reps"))
            upd_notes = request.form.get("upd_notes", "")
            new_1rm = round(upd_weight * (1 + float(upd_reps) / 30), 3)

            matching = next((row for row in user_data_exercise
                             if str(row["userId"]) == str(session["user_id"]) and
                             row["program"] == selected_prog and
                             row["exerciseName"] == selected_ex and
                             int(row["setNum"]) == selected_set and
                             row["date"] == orig_date and
                             float(row["weight"]) == float(orig_weight) and
                             int(row["reps"]) == int(orig_reps) and
                             str(row["notes"]) == str(orig_notes)), None)

            if matching:
                before = find_date(user_data_exercise, matching["id"], direction=-1)  # chronologically earlier
                after = find_date(user_data_exercise, matching["id"], direction=1)  # chronologically later
                new_diff = round(new_1rm - before["1rm"], 3) if before else 0
                new_diff_weight = round(upd_weight - before["weight"], 3) if before else 0

                updateLog(matching["id"], {
                    "date": upd_date,
                    "exerciseName": selected_ex,
                    "setNum": selected_set,
                    "weight": upd_weight,
                    "reps": upd_reps,
                    "1rm": new_1rm,
                    "diff": new_diff,
                    "diff_weight": new_diff_weight,
                    "notes": upd_notes
                })

                # print(before)

                if after:
                    # print("I love you king julian")
                    # print(after)
                    updateLog(after["id"], {
                        "diff": round(after["1rm"] - new_1rm, 3),
                        "diff_weight": round(after["weight"] - upd_weight, 3)
                    })

            success_message = "Log updated!"
            user_data_exercise = getUserLogs(session["user_id"])

    exercise_logs = [
        row for row in user_data_exercise
        if row["program"] == selected_prog
           and row["exerciseName"] == selected_ex
           and int(row["setNum"]) == selected_set
    ]
    visual_exercise_logs = [
        {**row, "date": iso_to_display(row["date"], date_format)}
        for row in exercise_logs
    ]

    stats = None
    chart_data = None
    if exercise_logs:
        import pandas as pd
        df = pd.DataFrame(exercise_logs)
        df["weight"] = pd.to_numeric(df["weight"])
        df["reps"] = pd.to_numeric(df["reps"])
        df["1rm"] = pd.to_numeric(df["1rm"])
        df["diff"] = pd.to_numeric(df["diff"])
        df["diff_weight"] = pd.to_numeric(df["diff_weight"])
        stats = {
            "best_1rm": round(df["1rm"].max(), 1),
            "avg_1rm": round(df["1rm"].mean(), 1),
            "best_weight": round(df["weight"].max(), 1),
            "avg_reps": round(df["reps"].mean(), 1),
            "count": len(df),
            "table": df[["weight", "reps", "1rm", "diff", "diff_weight"]].agg(
                ["mean", "std", "min", "max"]).round(2).to_dict(orient="index")
        }
        df["date_display"] = df["date"].apply(lambda d: iso_to_display(d, date_format))
        chart_data = df[["date", "date_display", "weight", "reps", "1rm", "diff", "diff_weight"]] \
            .sort_values("date").to_dict(orient="records")

    log_cap_warning = len(user_data_exercise) >= 1000

    return render_template("logs.html",
                           my_programs=my_programs,
                           selected_prog=selected_prog,
                           exercises=exercises,
                           exercise_names=exercise_names,
                           selected_ex=selected_ex,
                           num_sets=num_sets,
                           selected_unit=selected_unit,
                           selected_set=selected_set,
                           # exercise_logs=exercise_logs,
                           visual_exercise_logs=visual_exercise_logs,
                           exercise_data=exercise_data,
                           stats=stats,
                           chart_data=chart_data,
                           log_cap_warning=log_cap_warning,
                           success_message=success_message,
                           error_message=error_message)

@app.route("/logs/deleted", methods=["GET", "POST"])
def deleted_logs():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        action = request.form.get("action")
        all_logs = getAllLogs()

        if action == "delete_one":
            date = request.form.get("log_date")
            program = request.form.get("log_program")
            exercise = request.form.get("log_exercise")
            set_num = request.form.get("log_set")

            matching = [row for row in all_logs
                        if str(row["userId"]) == str(session["user_id"])
                        and int(row["status"]) == 0
                        and row["date"] == date
                        and row["program"] == program
                        and row["exerciseName"] == exercise
                        and str(row["setNum"]) == str(set_num)]
            if matching:
                deleteLog(matching[0]["id"])

        elif action == "clear_all":
            matching = [row for row in all_logs
                        if str(row["userId"]) == str(session["user_id"])
                        and int(row["status"]) == 0]
            for row in matching:
                deleteLog(row["id"])

        return redirect(url_for("deleted_logs"))

    date_format = session.get("settings", {}).get("date_format", 1)

    all_logs = getAllLogs()
    deleted = [
                {**row, "date": iso_to_display(row["date"], date_format)}
               for row in all_logs
               if str(row["userId"]) == str(session["user_id"])
               and int(row["status"]) == 0]

    return render_template("deleted_logs.html", deleted=deleted)

@app.route("/api/program_manifest")
def program_manifest():
    if "user_id" not in session:
        return jsonify({}), 401

    prog_data = getAllProgram()
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]

    # Structure: { "Push": { "Bench Press": 3, "Incline DB": 4 }, "Pull": { ... } }
    manifest = {}
    for row in user_prog:
        p_name = row["programName"]
        e_name = row["exerciseName"]
        if e_name.strip():  # Skip empty placeholder strings
            if p_name not in manifest:
                manifest[p_name] = {}
            manifest[p_name][e_name] = int(row["numSets"])

    return jsonify(manifest)

@app.route("/api/get_comparison_data")
def get_comparison_data():
    if "user_id" not in session:
        return jsonify([]), 401

    prog = request.args.get("program")
    ex = request.args.get("exercise")
    set_num = request.args.get("set_num")

    user_data = getUserLogs(session["user_id"])

    # Filter active logs matching selection
    logs = [
        {
            "date": row["date"],
            "weight": float(row["weight"]),
            "reps": int(row["reps"]),
            "1rm": float(row["1rm"]),
            "diff": float(row["diff"]),
            "diff_weight": float(row["diff_weight"])
        }
        for row in user_data
        if row["program"] == prog
           and row["exerciseName"] == ex
           and int(row["setNum"]) == int(set_num)
           and int(row.get("status", 1)) == 1
    ]

    # Chronological sort using your custom date style
    try:
        logs.sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"))
    except Exception:
        pass

    return jsonify(logs)

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)


