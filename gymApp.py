import streamlit as st
import pandas as pd
import bcrypt
import uuid
from programs import *
from sheets import *
from users import *
from activeUsers import *
from datetime import date
from streamlit_cookies_manager import EncryptedCookieManager

cookies = EncryptedCookieManager(prefix="gymtracker_", password=st.secrets["cookie_password"])
if not cookies.ready():
    st.stop()

users_sheet = getUsers()
users = getAllUsers(users_sheet)
tokens_sheet = getTokens()

# streamlit run gymApp.py

def hashPassword(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def checkPassword(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

st.title("Lifting Tracker")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# Login
if not st.session_state.logged_in:
    # Check for existing cookie on page load
    token = cookies.get("session_token")

    if token:
        matched = next((row for row in getAllTokens(tokens_sheet) if row["token"] == token), None)
        if matched:
            user = next((u for u in users if str(u["userId"]) == str(matched["userId"])), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()

    tab1, tab2 = st.tabs(["Login", "Create Account"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        remember_me = st.checkbox("Remember Me")
        if st.button("Login"):
            user = next((u for u in users if u["username"] == username), None)
            if user and checkPassword(password, user["password"]):
                st.session_state.logged_in = True
                st.session_state.user = user
                if remember_me:
                    token = str(uuid.uuid4())
                    appendToken(tokens_sheet, [token, user["userId"]])
                    cookies["session_token"] = token
                    cookies.save()
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab2:
        st.subheader("Create Account")
        new_username = st.text_input("Username", key="signup_user")
        new_password = st.text_input("Password", type="password", key="signup_pass1")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_pass2")
        if st.button("Create Account"):
            if not new_username or not new_password:
                st.warning("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords don't match.")
            elif any(u["username"] == new_username for u in users):
                st.error("Username already taken.")
            else:
                new_id = getNextUserId(users)
                appendUser(users_sheet, [new_username, hashPassword(new_password),new_id,])
                st.success("Account created! You can now log in.")
    st.markdown("---")

# Main App
else:
    user = st.session_state.user
    st.write(f"Welcome, {user['username']}!")
    st.write("Recent Update(s): Added ordering to programs, making it easier to customize the ordering of your "
             "programs.")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["My Programs", "Run Program", "Create Program", "Edit Programs", "Logs"])
    sheet = getLogs()
    data = getAllLogs(sheet)
    user_data = [row for row in data if str(row["userId"]) == str(user["userId"])]
    programs = getProgram()
    progData = getAllProgram(programs)
    userProg = [row for row in progData if str(row["userId"]) == str(user["userId"])]
    myPrograms = list(set(row["programName"] for row in userProg))
    maxExercises = 25

    with tab1:
        st.subheader("Your Programs")
        st.write("This panel displays all current programs you have created.")

        if len(myPrograms) > 0:
            for prog in myPrograms:
                st.markdown(f"### {prog}")
                exercises = [row for row in userProg if row["programName"] == prog]
                for ex in exercises:
                    st.write(
                        f"**{ex['exerciseName']}** — {ex['numSets']} sets, {ex['minReps']}–{ex['maxReps']} reps, "
                        f"{ex['increment']} lb increments")
                st.divider()
        else:
            st.write("No Programs Yet!")

    with tab2:
        if len(myPrograms) > 0:
            st.subheader("Run Program")
            selected = st.selectbox("Select a Program", myPrograms)
            exercises = [row for row in userProg if row["programName"] == selected]
            today = date.today().strftime("%m/%d/%Y")
            workoutDate = st.text_input("Date", value=today)
            st.write("This panel enters your lifts into our dataset. First you must have an available program to run, "
                     "after one has been made, select the program you with to run in the dropdown menu. After that, "
                     "simply enter the weight and reps for every set, and then click log set.")
            st.write('If you skip a set, simply do not click "Log Set" or if you wish, log 0 reps at 0 pounds.')


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

            for i in range(1, 25):
                for ex in exercises:
                    if i == ex['order']:
                        st.markdown(f"### {ex['exerciseName']}")
                        for j in range(ex['numSets']):
                            set_num = j + 1
                            st.markdown(f"**Set {set_num}**")
                            last = get_last_entry(user_data, selected, ex['exerciseName'], set_num)
                            if last:
                                st.caption(f"Last time you hit {last['weight']} lbs, for {last['reps']} reps.")
                                if last['reps'] >= ex['maxReps']:
                                    recWeight = last['weight'] + ex['increment'] + (int((last['weight'] - ex['maxReps'])
                                                                                        / 2) * ex['increment'])
                                    st.caption(f"Recommended weight is {recWeight} lbs, for {ex['minReps']} reps.")
                                elif last['reps'] <= ex['minReps'] - 1:
                                    st.caption(f"Recommended weight is "
                                               f"{last['weight'] - ex['increment']} lbs, for {ex['maxReps']} reps.")
                                else:
                                    st.caption(f"Recommended weight is {last['weight']} lbs, "
                                               f"for {last['reps'] + 1} reps.")
                            else:
                                st.caption("No previous entry found.")

                            col1, col2 = st.columns(2)
                            with col1:
                                reps = st.number_input(
                                    "Reps",
                                    min_value=0,
                                    max_value=100,
                                    value=int(last['reps']) if last else ex['minReps'],
                                    step=1,
                                    key=f"reps_{selected}_{ex['exerciseName']}_{set_num}"
                                )
                            with col2:
                                weight = st.number_input(
                                    "Weight",
                                    min_value=0.0,
                                    value=float(last['weight']) if last else 0.0,
                                    step=float(ex['increment']),
                                    key=f"weight_{selected}_{ex['exerciseName']}_{set_num}"
                                )

                            if st.button("Log Set", key=f"log_{ex['exerciseName']}_{set_num}"):
                                one_rm = round(weight * (1 + float(reps) / 30), 3)
                                diff = calculate_diff(user_data, selected, ex['exerciseName'], set_num, one_rm)
                                row = [int(user["userId"]), selected, workoutDate, ex['exerciseName'], set_num,
                                       float(weight), int(reps),
                                       one_rm, diff]
                                appendLogs(sheet, row)
                                st.success(f"Logged! 1RM estimate: {one_rm} | Diff: {diff}")

                        st.divider()
        else:
            st.write("No Programs Yet!")

    with tab3:
        st.subheader("Create Program")
        st.write('This panel lets you create your own programs, and add to them. To do this, enter the name of your '
                 'program then all the specific details of the first exercise, once everything is filled in, '
                 'then click "Add to Program". And repeat the process, not changing the name of your program, '
                 'until all exercises are entered.')

        program = st.text_input("Program (e.g. Legs, Push, Pull)")
        exercise = st.text_input("Exercise Name")
        set_num = st.number_input("Number of Sets", min_value=1, step=1)
        inc = st.number_input("Weight Increment", min_value=1.0)
        minReps = st.number_input("Minimum Number of Reps (Optional)", min_value=0, step=1)
        maxReps = st.number_input("Maximum Number of Reps (Optional)", min_value=minReps, step=1)
        exercises = [row for row in userProg if row["programName"] == program]
        nextOrder = 0

        if len(exercises) > 0:
            for i in range(len(exercises)):
                if exercises[i]['order'] > nextOrder:
                    nextOrder = exercises[i]['order'] # next order

        order = st.number_input("Order", min_value=1, max_value = maxExercises, value = nextOrder + 1, step=1)

        def isOpen(exercises, order):
            for i in range(len(exercises)):
                if exercises[i]['order'] == order:
                    return False
            return True

        if st.button("Add to Program"):
            if not program or not exercise:
                st.warning("Please fill in program and exercise name.")
            elif len(exercises) == maxExercises:
                st.warning("Cannot add any more exercises to this program.")
            elif not isOpen(exercises, order):
                st.warning("Cannot add exercise in that spot.")
            else:
                # cap program size at 25 exercises or so

                row = [int(user["userId"]), program, exercise, int(set_num), float(inc), int(minReps), int(maxReps),
                       int(order)]
                appendProgram(programs, row)

                for i in range(len(userProg)):
                    if userProg[i]["programName"] == program:
                        break
                    elif i == len(userProg) - 1:
                        st.success(f"New Program {program} created.")

                st.success(f"Added {exercise} to {program}!")

    with tab4:
        if len(myPrograms) > 0:
            st.subheader("Edit Programs")
            st.write('This panel lets you modify your existing programs, delete them, and add to them.')

            if not myPrograms:
                st.write("No programs found.")
            else:
                selected_edit = st.selectbox("Select a Program to Edit", myPrograms, key="edit_program_select")
                editExercises = [row for row in userProg if row["programName"] == selected_edit]

                st.markdown(f"### {selected_edit}")

                # Delete entire program button
                if st.button("Delete Entire Program", key="delete_program"):
                    all_rows = getAllProgram(programs)
                    for idx, row in enumerate(all_rows):
                        if str(row["userId"]) == str(user["userId"]) and row["programName"] == selected_edit:
                            programs.delete_rows(idx + 2)  # +2 because sheet is 1-indexed and has header row
                    st.success(f"Deleted program '{selected_edit}'!")
                    st.rerun()

                st.divider()

                # Add new exercise to this program
                with st.expander("Add Exercise to this Program"):
                    new_exercise = st.text_input("Exercise Name", key="edit_new_exercise")
                    new_sets = st.number_input("Number of Sets", min_value=1, step=1, key="edit_new_sets")
                    new_inc = st.number_input("Weight Increment", min_value=0.5, step=0.5, key="edit_new_inc")
                    new_min = st.number_input("Min Reps", min_value=0, step=1, key="edit_new_min")
                    new_max = st.number_input("Max Reps", min_value=0, step=1, key="edit_new_max")

                    nextOrder = 0

                    if len(editExercises) > 0:
                        for i in range(len(editExercises)):
                            if editExercises[i]['order'] > nextOrder:
                                nextOrder = editExercises[i]['order']

                    new_order = st.number_input("Order", min_value=1, max_value= maxExercises,
                                                value=nextOrder + 1,step=1, key="edit_new_order")
                    if st.button("Add Exercise", key="edit_add_exercise"):


                        if not new_exercise:
                            st.warning("Please enter an exercise name.")
                        else:
                            for i in range(len(editExercises)):
                                if editExercises[i]['order'] == new_order:
                                    editExercises[i]['order'] = nextOrder


                            row = [int(user["userId"]), selected_edit, new_exercise, int(new_sets), float(new_inc),
                                   int(new_min), int(new_max), int(new_order)]
                            appendLogs(programs, row)
                            st.success(f"Swapped order values for exercise '{editExercises[i]['exerciseName']}' "
                                       f"and '{editExercises[i]["exerciseName"]}'.")
                            st.success(f"Added {new_exercise} to {selected_edit}!")
                            st.rerun()

                st.divider()

                # Table of exercises with edit/delete buttons
                for ex in editExercises:
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(
                            f"**{ex['exerciseName']}** — {ex['numSets']} sets, {ex['minReps']}–{ex['maxReps']} reps, "
                            f"{ex['increment']} lb increments, exercise number {ex['order']}")

                    with col2:
                        if st.button("Edit", key=f"edit_{ex['exerciseName']}"):
                            st.session_state[f"editing_{ex['exerciseName']}"] = True

                    with col3:
                        if st.button("Delete", key=f"delete_{ex['exerciseName']}"):
                            all_rows = getAllProgram(programs)
                            indices_to_delete = [idx + 2 for idx, row in enumerate(all_rows)
                                                 if (str(row["userId"]) == str(user["userId"]) and
                                                     row["programName"] == selected_edit and
                                                     row["exerciseName"] == ex["exerciseName"])]
                            for idx in reversed(indices_to_delete):
                                programs.delete_rows(idx)
                            st.success(f"Deleted {ex['exerciseName']}!")
                            st.rerun()

                    # Inline edit form
                    if st.session_state.get(f"editing_{ex['exerciseName']}", False):
                        with st.expander(f"Editing {ex['exerciseName']}", expanded=True):
                            upd_sets = st.number_input("Number of Sets", value=int(ex['numSets']), step=1,
                                                       key=f"upd_sets_{ex['exerciseName']}")
                            upd_inc = st.number_input("Weight Increment", value=float(ex['increment']), step=0.5,
                                                      key=f"upd_inc_{ex['exerciseName']}")
                            upd_min = st.number_input("Min Reps", value=int(ex['minReps']), step=1,
                                                      key=f"upd_min_{ex['exerciseName']}")
                            upd_max = st.number_input("Max Reps", value=int(ex['maxReps']), step=1,
                                                      key=f"upd_max_{ex['exerciseName']}")
                            nextOrder = 0
                            if len(editExercises) > 0:
                                for i in range(len(editExercises)):
                                    if editExercises[i]['order'] > nextOrder:
                                        nextOrder = editExercises[i]['order']

                            upd_order = st.number_input("Order", min_value=1, max_value=maxExercises,
                                                        value=nextOrder, step=1, key=f"upd_order_{ex['exerciseName']}")

                            for i in range(len(editExercises)):
                                if editExercises[i]['order'] == upd_order:
                                    editExercises[i]['order'] = nextOrder


                            if st.button("Save Changes", key=f"save_{ex['exerciseName']}"):
                                all_rows = getAllProgram(programs)
                                for idx, row in enumerate(all_rows):
                                    if (str(row["userId"]) == str(user["userId"]) and
                                            row["programName"] == selected_edit and
                                            row["exerciseName"] == ex["exerciseName"]):
                                        programs.update(f"D{idx + 2}:H{idx + 2}",
                                                        [[int(upd_sets), float(upd_inc), int(upd_min), int(upd_max),
                                                          int(upd_order)]])
                                st.session_state[f"editing_{ex['exerciseName']}"] = False
                                st.success(f"Swapped order values for exercise '{editExercises[i]['exerciseName']}' "
                                           f"and '{editExercises[i]["exerciseName"]}'.")
                                st.success("Changes saved!")
                                st.rerun()

                            if st.button("Cancel", key=f"cancel_{ex['exerciseName']}"):
                                st.session_state[f"editing_{ex['exerciseName']}"] = False
                                st.rerun()

                    st.divider()
        else:
            st.write("No Programs Yet!")

                #streamlit run gymApp.py

    with tab5:
        if len(myPrograms) > 0:
            st.subheader("Stats")
            st.write('This panel lets you see the small details and statistics behind your lifts, select the program '
                     'you wish to look at, then the specific exercise, and then the set.')
            selectedProg = st.selectbox("Select Program", myPrograms, key="stats_prog")
            exercises = [row for row in userProg if row["programName"] == selectedProg]
            exerciseNames = [row["exerciseName"] for row in exercises]
            selectedEx = st.selectbox("Select Exercise", exerciseNames, key="stats_ex")
            exerciseData = next(row for row in exercises if row["exerciseName"] == selectedEx)
            numSets = int(exerciseData["numSets"])
            selectedSet = st.number_input("Set Number", min_value=1, max_value=numSets, step=1, key="stats_set")

            exerciseLogs = [row for row in user_data if (row["program"] == selectedProg) and
                            (row["exerciseName"] == selectedEx) and (int(row["setNum"]) == int(selectedSet))]

            if not exerciseLogs:
                st.info("No logs found for this exercise and set.")
            else:
                df = pd.DataFrame(exerciseLogs)
                df["weight"] = pd.to_numeric(df["weight"])
                df["reps"] = pd.to_numeric(df["reps"])
                df["1rm"] = pd.to_numeric(df["1rm"])
                df["diff"] = pd.to_numeric(df["diff"])

                st.markdown(f"### {selectedEx} — Set {int(selectedSet)}")
                st.caption(f"{len(df)} logged sessions")

                # Top metric cards
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Best 1RM", f"{df['1rm'].max():.1f}")
                with col2:
                    st.metric("Avg 1RM", f"{df['1rm'].mean():.1f}")
                with col3:
                    st.metric("Best Weight", f"{df['weight'].max():.1f}")
                with col4:
                    st.metric("Avg Reps", f"{df['reps'].mean():.1f}")

                st.divider()

                # Summary stats table
                st.markdown("#### Summary Statistics")
                cols = ["weight", "reps", "1rm", "diff"]
                stats_df = df[cols].agg(["mean", "std", "min", "max"]).T
                stats_df.columns = ["Mean", "Std Dev", "Min", "Max"]
                stats_df["Q1"] = df[cols].quantile(0.25)
                stats_df["Median"] = df[cols].quantile(0.50)
                stats_df["Q3"] = df[cols].quantile(0.75)
                stats_df = stats_df[["Min", "Q1", "Median", "Mean", "Q3", "Max", "Std Dev"]]
                stats_df = stats_df.round(2)
                st.dataframe(stats_df, use_container_width=True)

                st.divider()

                # 1RM over time chart
                st.markdown("#### 1RM Over Time")
                chart_df = df[["date", "1rm"]].copy()
                chart_df["date"] = pd.to_datetime(chart_df["date"])
                chart_df = chart_df.sort_values("date")
                st.line_chart(chart_df.set_index("date")["1rm"])
        else:
            st.write("No Programs Yet!")

st.caption("Developed by Erik Afdahl")
st.caption('For customer service questions, error messages, and any and all feedback '
           'email "erik.afdahl.1@gmail.com"')