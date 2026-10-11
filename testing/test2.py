edit_exercises = [[1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6]]

changing = int(input("Changing: "))
upd_order = int(input("New order: "))
open_order = 1

for ex in edit_exercises:
    if ex[0] - 1 != open_order:
        open_order += 1
    else:
        break

print(open_order)

orig_order = changing #next(e["order"] for e in edit_exercises if e["exerciseName"] == exercise_name)
# open_order
for ex in edit_exercises:
    if ex == changing: # check name not number
        continue
    elif (ex[0] <= upd_order) and (ex[0] > orig_order):
        edit_exercises[ex[0] - 1][0] = edit_exercises[ex[0] - 1][0] - 1
    elif (ex[0] >= upd_order) and (ex[0] < orig_order):
        edit_exercises[ex[0] - 1][0] = edit_exercises[ex[0] - 1][0] + 1

edit_exercises[changing - 1][0] = upd_order

for i in edit_exercises:
    print(i)
    # if int(ex) >= upd_order:

    # elif (int(ex["order"]) > orig_order) and (int(ex["order"]) < upd_order):
