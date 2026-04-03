from flask import Flask, render_template, request, redirect, url_for, session
from datetime import timedelta, date
import bcrypt
import uuid
from sheets import *
from users import *
from programs import *
from activeUsers import *

# python liftingTracker/lsdapp.py

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.permanent_session_lifetime = timedelta(days=30)

def hashPassword(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def checkPassword(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def isOpen(exercises, order):
    for i in range(len(exercises)):
        if exercises[i]['order'] == order:
            return False
    return True

def calculate_diff(data, program, exercise, set_num, current_1rm):
    for row in reversed(data):
        if (row["program"] == program and
                row["exerciseName"] == exercise and
                int(row["setNum"]) == int(set_num)):
            return round(current_1rm - float(row["1rm"]), 3)
    return 0

def get_last_entry(data, program, exercise, set_num):
    for row in reversed(data):
        if (row["program"] == program and
                row["exerciseName"] == exercise and
                int(row["setNum"]) == int(set_num)):
            return row
    return None
@app.route("/", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    error = None
    if request.method == "POST":
        action = request.form.get("action")
        users_sheet = getUsers()
        users = getAllUsers(users_sheet)

        if action == "login":
            username = request.form.get("username")
            password = request.form.get("password")
            remember = request.form.get("remember_me")
            user = next((u for u in users if u["username"] == username), None)
            if user and checkPassword(password, user["password"]):
                session.permanent = True
                session["user_id"] = user["userId"]
                session["username"] = user["username"]
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
                new_id = getNextUserId(users)
                appendUser(users_sheet, [new_username, hashPassword(new_password), new_id])
                error = "Account created! You can now log in."

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    programs_sheet = getProgram()
    prog_data = getAllProgram(programs_sheet)
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog))
    logs_sheet = getLogs()
    user_data = [row for row in getAllLogs(logs_sheet) if str(row["userId"]) == str(session["user_id"])]

    return render_template("home.html",
                           username=session["username"],
                           user_prog=user_prog,
                           my_programs=my_programs,
                           user_data=user_data,)

@app.route("/run", methods=["GET", "POST"])
def run():
    if "user_id" not in session:
        return redirect(url_for("login"))

    programs_sheet = getProgram()
    prog_data = getAllProgram(programs_sheet)
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog))

    logs_sheet = getLogs()
    user_data = [row for row in getAllLogs(logs_sheet) if str(row["userId"]) == str(session["user_id"])]

    if not my_programs:
        return render_template("run.html", my_programs=[], exercises=[], user_data=[], selected=None, today="")

    selected = request.args.get("program") or request.form.get("selected_program")
    if not selected or selected not in my_programs:
        last_program = user_data[-1]["program"] if user_data else None
        selected = last_program if last_program in my_programs else my_programs[0]

    exercises = sorted(
        [row for row in user_prog if row["programName"] == selected],
        key=lambda x: int(x["order"])
    )

    today = date.today().strftime("%m/%d/%Y")
    success_message = None

    # Get current exercise index
    ex_index = request.args.get("ex_index", type=int)

    if ex_index is None:
        programLogs = [row for row in user_data if row["program"] == selected]
        last_ex = programLogs[-1]["exerciseName"] if programLogs else None
        if last_ex:
            match = next((e for e in exercises if e["exerciseName"] == last_ex), None)
            ex_index = (int(match["order"]) % len(exercises)) if match else 0
        else:
            ex_index = 0

    ex_index = max(0, min(ex_index, len(exercises) - 1))

    if request.method == "POST" and request.form.get("action") == "log_set":
        exercise_name = request.form.get("exercise_name")
        set_num = int(request.form.get("set_num"))
        weight = float(request.form.get("weight"))
        reps = int(request.form.get("reps"))
        notes = request.form.get("notes", "")
        workout_date = request.form.get("workout_date")
        selected = request.form.get("selected_program")

        one_rm = round(weight * (1 + float(reps) / 30), 3)
        diff = calculate_diff(user_data, selected, exercise_name, set_num, one_rm)
        row = [int(session["user_id"]), selected, workout_date, exercise_name,
               set_num, weight, reps, one_rm, diff, notes]
        appendLogs(logs_sheet, row)
        success_message = f"Logged {exercise_name} Set {set_num} — 1RM: {one_rm} | Diff: {diff}"

        user_data = [row for row in getAllLogs(logs_sheet) if str(row["userId"]) == str(session["user_id"])]
        exercises = sorted(
            [row for row in user_prog if row["programName"] == selected],
            key=lambda x: int(x["order"])
        ) # funky

    # Build last entry lookup and recommendations for all exercises
    last_entries = {}
    recommendations = {}
    for ex in exercises:
        for s in range(1, int(ex["numSets"]) + 1):
            key = f"{ex['exerciseName']}_{s}"
            last_entries[key] = get_last_entry(user_data, selected, ex["exerciseName"], s)
            last = last_entries[key]
            if last:
                if int(last["reps"]) >= int(ex["maxReps"]):
                    rec_weight = round((last["1rm"]/(1 + (ex["minReps"]/30)) - last["weight"]) /
                                       ex["increment"]) * ex["increment"] + last["weight"]

                    # rec_weight = float(last["weight"]) + float(ex["increment"]) + (
                    #     int((int(last["reps"]) - int(ex["maxReps"])) / 2) * float(ex["increment"]))
                    recommendations[key] = f"Recommended: {rec_weight} lbs for {ex['minReps']} reps"
                elif int(last["reps"]) <= int(ex["minReps"]) - 1:
                    rec_weight = float(last["weight"]) - float(ex["increment"])
                    recommendations[key] = f"Recommended: {rec_weight} lbs for {ex['maxReps']} reps"
                else:
                    recommendations[key] = f"Recommended: {last['weight']} lbs for {int(last['reps']) + 1} reps"

    return render_template("run.html",
                           my_programs=my_programs,
                           selected=selected,
                           exercises=exercises,
                           ex_index=ex_index,
                           today=today,
                           last_entries=last_entries,
                           recommendations=recommendations,
                           success_message=success_message,
                           user_data=user_data)

@app.route("/manage", methods=["GET", "POST"])
def manage():
    if "user_id" not in session:
        return redirect(url_for("login"))

    programs_sheet = getProgram()
    prog_data = getAllProgram(programs_sheet)
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog))

    max_exercises = 25
    success_message = None
    error_message = None

    selected_edit = request.args.get("program") or request.form.get("selected_program")
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
                # Actually persist the program by writing a placeholder row
                placeholder_row = [int(session["user_id"]), new_program_name, "", 0, 0, 0, 0, 0, ""]
                appendProgram(programs_sheet, placeholder_row)

                my_programs.append(new_program_name)
                selected_edit = new_program_name
                success_message = f"Program '{new_program_name}' created! Now add exercises to it."

        elif action == "delete_program":
            all_rows = getAllProgram(programs_sheet)
            indices = [idx + 2 for idx, row in enumerate(all_rows)
                       if str(row["userId"]) == str(session["user_id"])
                       and row["programName"] == selected_edit]
            for idx in reversed(indices):
                programs_sheet.delete_rows(idx)
            success_message = f"Deleted program '{selected_edit}'!"
            my_programs = [p for p in my_programs if p != selected_edit]
            selected_edit = my_programs[0] if my_programs else None
            prog_data = getAllProgram(programs_sheet)
            user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]

        elif action == "add_exercise":
            new_exercise = request.form.get("new_exercise", "").strip()
            new_sets = int(request.form.get("new_sets", 1))
            new_inc = float(request.form.get("new_inc", 5.0))
            new_min = int(request.form.get("new_min", 6))
            new_max = int(request.form.get("new_max", 8))
            new_notes = request.form.get("new_notes", "")
            new_order = int(request.form.get("new_order", 1))
            edit_exercises = [row for row in user_prog if row["programName"] == selected_edit]

            if not new_exercise:
                error_message = "Please enter an exercise name."
            elif new_max < new_min:
                error_message = "Minimum reps must be less than or equal to maximum reps."
            else:
                # Handle order conflict
                all_rows = getAllProgram(programs_sheet)
                for ex in edit_exercises:
                    if int(ex["order"]) == new_order:
                        next_order = max(int(e["order"]) for e in edit_exercises) + 1
                        for idx, row in enumerate(all_rows):
                            if (str(row["userId"]) == str(session["user_id"]) and
                                    row["programName"] == selected_edit and
                                    row["exerciseName"] == ex["exerciseName"]):
                                programs_sheet.update(f"H{idx + 2}", [[next_order]])
                        break

                row = [int(session["user_id"]), selected_edit, new_exercise, new_sets,
                       new_inc, new_min, new_max, new_order, new_notes]
                appendProgram(programs_sheet, row)
                success_message = f"Added {new_exercise} to {selected_edit}!"
                prog_data = getAllProgram(programs_sheet)
                user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]

        elif action == "delete_exercise":
            exercise_name = request.form.get("exercise_name")
            all_rows = getAllProgram(programs_sheet)
            indices = [idx + 2 for idx, row in enumerate(all_rows)
                       if (str(row["userId"]) == str(session["user_id"]) and
                           row["programName"] == selected_edit and
                           row["exerciseName"] == exercise_name)]
            for idx in reversed(indices):
                programs_sheet.delete_rows(idx)
            success_message = f"Deleted {exercise_name}!"
            prog_data = getAllProgram(programs_sheet)
            user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]

        elif action == "save_exercise":
            exercise_name = request.form.get("exercise_name")
            upd_sets = int(request.form.get("upd_sets"))
            upd_inc = float(request.form.get("upd_inc"))
            upd_min = int(request.form.get("upd_min"))
            upd_max = int(request.form.get("upd_max"))
            upd_notes = request.form.get("upd_notes", "")
            upd_order = int(request.form.get("upd_order"))
            edit_exercises = [row for row in user_prog if row["programName"] == selected_edit]
            all_rows = getAllProgram(programs_sheet)

            # Handle order conflict
            swapped_name = None
            for ex in edit_exercises:
                if int(ex["order"]) == upd_order and ex["exerciseName"] != exercise_name:
                    swapped_name = ex["exerciseName"]
                    orig_order = next(e["order"] for e in edit_exercises if e["exerciseName"] == exercise_name)
                    for idx, row in enumerate(all_rows):
                        if (str(row["userId"]) == str(session["user_id"]) and
                                row["programName"] == selected_edit and
                                row["exerciseName"] == swapped_name):
                            programs_sheet.update(f"H{idx + 2}", [[int(orig_order)]])
                    break

            for idx, row in enumerate(all_rows):
                if (str(row["userId"]) == str(session["user_id"]) and
                        row["programName"] == selected_edit and
                        row["exerciseName"] == exercise_name):
                    programs_sheet.update(f"D{idx + 2}:I{idx + 2}",
                                          [[upd_sets, upd_inc, upd_min, upd_max, upd_order, upd_notes]])

            success_message = f"Saved changes to {exercise_name}!"
            if swapped_name:
                success_message += f" Swapped order with '{swapped_name}'."
            prog_data = getAllProgram(programs_sheet)
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
                           success_message=success_message,
                           error_message=error_message)

@app.route("/logs", methods=["GET", "POST"])
def logs():
    if "user_id" not in session:
        return redirect(url_for("login"))

    programs_sheet = getProgram()
    prog_data = getAllProgram(programs_sheet)
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog))

    logs_sheet = getLogs()
    user_data = [row for row in getAllLogs(logs_sheet) if str(row["userId"]) == str(session["user_id"])]

    success_message = None
    error_message = None

    selected_prog = request.args.get("program") or request.form.get("selected_prog")
    if not selected_prog or selected_prog not in my_programs:
        selected_prog = my_programs[0] if my_programs else None

    selected_ex = request.args.get("exercise") or request.form.get("selected_ex")
    exercises = [row for row in user_prog if row["programName"] == selected_prog]
    exercise_names = [row["exerciseName"] for row in exercises]
    if not selected_ex or selected_ex not in exercise_names:
        selected_ex = exercise_names[0] if exercise_names else None

    exercise_data = next((row for row in exercises if row["exerciseName"] == selected_ex), None)
    num_sets = int(exercise_data["numSets"]) if exercise_data else 1

    selected_set = int(request.args.get("set_num") or request.form.get("selected_set") or 1)
    if selected_set < 1:
        selected_set = 1
    if selected_set > num_sets:
        selected_set = num_sets

    action = request.form.get("action")

    if request.method == "POST":
        if action == "delete_log":
            log_date = request.form.get("log_date")
            log_weight = request.form.get("log_weight")
            log_reps = request.form.get("log_reps")
            log_notes = request.form.get("log_notes")
            all_logs = getAllLogs(logs_sheet)
            indices = [idx + 2 for idx, row in enumerate(all_logs)
                       if (str(row["userId"]) == str(session["user_id"]) and
                           row["program"] == selected_prog and
                           row["exerciseName"] == selected_ex and
                           int(row["setNum"]) == selected_set and
                           row["date"] == log_date and
                           float(row["weight"]) == float(log_weight) and
                           int(row["reps"]) == int(log_reps) and
                           str(row["notes"]) == str(log_notes))]
            for idx in reversed(indices):
                logs_sheet.delete_rows(idx)
            success_message = "Log deleted!"
            user_data = [row for row in getAllLogs(logs_sheet) if str(row["userId"]) == str(session["user_id"])]

        elif action == "save_log":
            orig_date = request.form.get("orig_date")
            orig_weight = request.form.get("orig_weight")
            orig_reps = request.form.get("orig_reps")
            orig_notes = request.form.get("orig_notes")
            upd_date = request.form.get("upd_date")
            upd_weight = float(request.form.get("upd_weight"))
            upd_reps = int(request.form.get("upd_reps"))
            upd_notes = request.form.get("upd_notes", "")
            new_1rm = round(upd_weight * (1 + float(upd_reps) / 30), 3)
            all_logs = getAllLogs(logs_sheet)
            for idx, row in enumerate(all_logs):
                if (str(row["userId"]) == str(session["user_id"]) and
                        row["program"] == selected_prog and
                        row["exerciseName"] == selected_ex and
                        int(row["setNum"]) == selected_set and
                        row["date"] == orig_date and
                        float(row["weight"]) == float(orig_weight) and
                        int(row["reps"]) == int(orig_reps) and
                        str(row["notes"]) == str(orig_notes)):
                    logs_sheet.update(f"C{idx + 2}:J{idx + 2}",
                                      [[upd_date, selected_ex, selected_set,
                                        upd_weight, upd_reps, new_1rm, 0, upd_notes]])
            success_message = "Log updated!"
            user_data = [row for row in getAllLogs(logs_sheet) if str(row["userId"]) == str(session["user_id"])]

    exercise_logs = [row for row in user_data if
                     row["program"] == selected_prog and
                     row["exerciseName"] == selected_ex and
                     int(row["setNum"]) == selected_set]

    # Build stats
    stats = None
    chart_data = None
    if exercise_logs:
        import pandas as pd
        df = pd.DataFrame(exercise_logs)
        df["weight"] = pd.to_numeric(df["weight"])
        df["reps"] = pd.to_numeric(df["reps"])
        df["1rm"] = pd.to_numeric(df["1rm"])
        df["diff"] = pd.to_numeric(df["diff"])
        stats = {
            "best_1rm": round(df["1rm"].max(), 1),
            "avg_1rm": round(df["1rm"].mean(), 1),
            "best_weight": round(df["weight"].max(), 1),
            "avg_reps": round(df["reps"].mean(), 1),
            "count": len(df),
            "table": df[["weight", "reps", "1rm", "diff"]].agg(["mean", "std", "min", "max"]).round(2).to_dict(orient="index")
        }
        chart_data = df[["date", "weight", "reps", "1rm", "diff"]].sort_values("date").to_dict(orient="records")

    return render_template("logs.html",
                           my_programs=my_programs,
                           selected_prog=selected_prog,
                           exercises=exercises,
                           exercise_names=exercise_names,
                           selected_ex=selected_ex,
                           num_sets=num_sets,
                           selected_set=selected_set,
                           exercise_logs=exercise_logs,
                           exercise_data=exercise_data,
                           stats=stats,
                           chart_data=chart_data,
                           success_message=success_message,
                           error_message=error_message)

if __name__ == "__main__":
    app.run(debug=True)