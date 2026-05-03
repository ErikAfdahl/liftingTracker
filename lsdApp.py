from flask import Flask, render_template, request, redirect, url_for, session
from datetime import *
import pytz
import bcrypt
import uuid
from db import *

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

def get_last_entry(data, program, exercise, set_num, back = 0):
    acc = 0
    for row in reversed(data):
        if (row["program"] == program and row["exerciseName"] == exercise and
                int(row["setNum"]) == int(set_num)):
            if acc == back:
                return row
            acc += 1

    return None
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
                    "quick_indexing": 1
                })
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

    prog_data = getAllProgram()
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog))
    user_data = [row for row in getAllLogs() if str(row["userId"]) == str(session["user_id"])]

    return render_template("home.html",
                           username=session["username"],
                           user_prog=user_prog,
                           my_programs=my_programs,
                           user_data=user_data)

@app.route("/run", methods=["GET", "POST"])
def run():
    if "user_id" not in session:
        return redirect(url_for("login"))

    prog_data = getAllProgram()
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog if row["programName"] != " "))

    user_data = [row for row in getAllLogs() if str(row["userId"]) == str(session["user_id"])]

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
    today = now.strftime("%m/%d/%Y")
    success_message = None

    ex_index = request.args.get("ex_index", type=int)

    if ex_index is None:
        programLogs = [row for row in user_data if row["program"] == selected]
        last = programLogs[-1] if programLogs else None

        if last:
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
        exercise_name = request.form.get("exercise_name")
        set_num = int(request.form.get("set_num"))
        weight = float(request.form.get("weight"))
        reps = int(request.form.get("reps"))
        notes = request.form.get("notes", "")
        workout_date = request.form.get("workout_date")
        selected = request.form.get("selected_program")

        one_rm = round(weight * (1 + float(reps) / 30), 3)
        diff = calculate_diff(user_data, selected, exercise_name, set_num, one_rm)

        appendLog({
            "userId": int(session["user_id"]),
            "program": selected,
            "status": 1,
            "date": workout_date,
            "exerciseName": exercise_name,
            "setNum": set_num,
            "weight": weight,
            "reps": reps,
            "1rm": one_rm,
            "diff": diff,
            "notes": notes
        })

        narrator = session.get("settings", {}).get("narrator", "default")
        if narrator == "mommy":
            success_message = f"Good job sweetie! Set {set_num} logged — 1RM: {one_rm} | Diff: {diff}"
        elif narrator == "hard":
            success_message = f"Alright I wrote that down, but don't get your hopes up. Set {set_num} logged — 1RM: {one_rm} | Diff: {diff}"
        else:
            success_message = f"Logged {exercise_name} Set {set_num} — 1RM: {one_rm} | Diff: {diff}"

        user_data = [row for row in getAllLogs() if str(row["userId"]) == str(session["user_id"])]
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

    last_entries = {}
    recommendations = {}
    for ex in exercises:
        for s in range(1, int(ex["numSets"]) + 1):
            key = f"{ex['exerciseName']}_{s}"
            last_entries[key] = get_last_entry(user_data, selected, ex["exerciseName"], s)
            last = last_entries[key]
            if last:
                if int(last["reps"]) >= int(ex["maxReps"]) + 2:
                    rec_weight = round((last["1rm"]/(1 + (ex["minReps"]/30)) - last["weight"]) /
                                       ex["increment"]) * ex["increment"] + last["weight"]
                elif int(last["reps"]) >= int(ex["maxReps"]):
                    rec_weight = float(last["weight"]) + float(ex["increment"])
                    recommendations[key] = f"Recommended: {rec_weight} lbs for {ex['minReps']} reps"
                elif int(last["reps"]) < int(ex["minReps"]) - 1:
                    rec_weight = float(last["weight"]) - float(ex["increment"])
                    recommendations[key] = f"Recommended: {rec_weight} lbs for {ex['maxReps']} reps"
                else:
                    recommendations[key] = f"Recommended: {last['weight']} lbs for {int(last['reps']) + 1} reps"

    prev_entries = {}
    for ex in exercises:
        for set_num in range(1, int(ex["numSets"]) + 1):
            key = f"{ex['exerciseName']}_{set_num}"
            prev_entries[key] = get_last_entry(user_data, selected, ex["exerciseName"], set_num, back=1)

    return render_template("run.html",
                           my_programs=my_programs,
                           selected=selected,
                           exercises=exercises,
                           ex_index=ex_index,
                           today=today,
                           last_entries=last_entries,
                           prev_entries=prev_entries,
                           recommendations=recommendations,
                           success_message=success_message,
                           user_data=user_data)

@app.route("/run/results")
def run_results():
    if "user_id" not in session:
        return redirect(url_for("login"))

    selected = request.args.get("program")

    prog_data = getAllProgram()
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]

    exercises = sorted(
        [row for row in user_prog if row["programName"] == selected],
        key=lambda x: int(x["order"])
    )

    user_data = [row for row in getAllLogs() if str(row["userId"]) == str(session["user_id"])]

    last_entries = {}
    prev_entries = {}
    for ex in exercises:
        for s in range(1, int(ex["numSets"]) + 1):
            key = f"{ex['exerciseName']}_{s}"
            last_entries[key] = get_last_entry(user_data, selected, ex["exerciseName"], s, back=0)
            prev_entries[key] = get_last_entry(user_data, selected, ex["exerciseName"], s, back=1)

    return render_template("results.html",
                           selected=selected,
                           exercises=exercises,
                           last_entries=last_entries,
                           prev_entries=prev_entries,
                           narrator=session.get("settings", {}).get("narrator", "default"))

@app.route("/manage", methods=["GET", "POST"])
def manage():
    if "user_id" not in session:
        return redirect(url_for("login"))

    prog_data = getAllProgram()
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog))
    user_data = [row for row in getAllLogs() if str(row["userId"]) == str(session["user_id"])]

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
                appendProgram({
                    "userId": int(session["user_id"]),
                    "programName": new_program_name,
                    "exerciseName": "",
                    "numSets": 0,
                    "increment": 0,
                    "minReps": 0,
                    "maxReps": 0,
                    "order": 0,
                    "notes": ""
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
                    "minReps": new_min,
                    "maxReps": new_max,
                    "order": new_order,
                    "notes": new_notes
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
            upd_min = int(request.form.get("upd_min"))
            upd_max = int(request.form.get("upd_max"))
            upd_notes = request.form.get("upd_notes", "")
            upd_order = int(request.form.get("upd_order"))
            edit_exercises = [row for row in user_prog if row["programName"] == selected_edit]

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
                    "minReps": upd_min,
                    "maxReps": upd_max,
                    "order": upd_order,
                    "notes": upd_notes
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
                           success_message=success_message,
                           error_message=error_message)

@app.route("/logs", methods=["GET", "POST"])
def logs():
    if "user_id" not in session:
        return redirect(url_for("login"))

    prog_data = getAllProgram()
    user_prog = [row for row in prog_data if str(row["userId"]) == str(session["user_id"])]
    my_programs = list(set(row["programName"] for row in user_prog))

    user_data = [row for row in getAllLogs() if str(row["userId"]) == str(session["user_id"])]

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

            matching = [row for row in user_data
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
            user_data = [row for row in getAllLogs() if str(row["userId"]) == str(session["user_id"])]

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

            matching = next((row for row in user_data
                             if str(row["userId"]) == str(session["user_id"]) and
                             row["program"] == selected_prog and
                             row["exerciseName"] == selected_ex and
                             int(row["setNum"]) == selected_set and
                             row["date"] == orig_date and
                             float(row["weight"]) == float(orig_weight) and
                             int(row["reps"]) == int(orig_reps) and
                             str(row["notes"]) == str(orig_notes)), None)
            if matching:
                updateLog(matching["id"], {
                    "date": upd_date,
                    "exerciseName": selected_ex,
                    "setNum": selected_set,
                    "weight": upd_weight,
                    "reps": upd_reps,
                    "1rm": new_1rm,
                    "diff": 0,
                    "notes": upd_notes
                })
            success_message = "Log updated!"
            user_data = [row for row in getAllLogs() if str(row["userId"]) == str(session["user_id"])]

    exercise_logs = [row for row in user_data if
                     row["program"] == selected_prog and
                     row["exerciseName"] == selected_ex and
                     int(row["setNum"]) == selected_set]

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
            "table": df[["weight", "reps", "1rm", "diff"]].agg(
                ["mean", "std", "min", "max"]).round(2).to_dict(orient="index")
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
            for row in matching:
                deleteLog(row["id"])

        elif action == "clear_all":
            matching = [row for row in all_logs
                        if str(row["userId"]) == str(session["user_id"])
                        and int(row["status"]) == 0]
            for row in matching:
                deleteLog(row["id"])

        return redirect(url_for("deleted_logs"))

    all_logs = getAllLogs()
    deleted = [row for row in all_logs
               if str(row["userId"]) == str(session["user_id"])
               and int(row["status"]) == 0]

    return render_template("deleted_logs.html", deleted=deleted)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST" and request.form.get("action") == "save_settings":
        narrator = request.form.get("narrator", "default")
        quick_indexing = 1 if request.form.get("quick_indexing") else 0

        updateUser(session["user_id"], {
            "narrator": narrator,
            "quick_indexing": quick_indexing
        })

        session["settings"] = {
            "narrator": narrator,
            "quick_indexing": bool(quick_indexing),
        }

        return redirect(url_for("settings", success=1))

    success_message = "Settings saved!" if request.args.get("success") else None

    users = getAllUsers()
    user = next((u for u in users if str(u["userId"]) == str(session["user_id"])), None)

    settings = {
        "narrator": user.get("narrator", "default") if user else "default",
        "quick_indexing": bool(int(user.get("quick_indexing", 1))) if user else True,
    }

    return render_template("settings.html", settings=settings, success_message=success_message)


if __name__ == "__main__":
    app.run(debug=True)


# to do list
# fix ordering issues when deleting an exercise