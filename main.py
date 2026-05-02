from datetime import date

def checkType(value, type, message: str, min = 0):
    """
    This function is to make sure the user inputs the correct value type, and converts value types
    :param value: the entered value
    :param type: the type of value needed
    :param message: input message
    :param min: minimum value the value should be
    :return: fixed value
    """
    while True:
        try:
            if type == "int":
                value = int(value)
                if value >= min:
                    return value
                else:
                    print(f"Invalid Input, must be more or equal to {min}.")
                    value = input(message)
            elif type == "float":
                value = float(value)
                if value >= min:
                    return value
                else:
                    print(f"Invalid Input, must be more or equal to {min}.")
                    value = input(message)
            elif type == "str":
                return str(value)
        except ValueError:
            print("Invalid Input")
            value = input(message)

def createProgram() -> list:
    """
    This function is to create the program
    :return: list of exercise and number of sets and other stuff
    """
    program = []
    para = ["Program Name", "Exercise Name", "Number of Sets", "Incriment", "Min Reps", "Max Reps"]
    paraTyoe = ["str", "str", "int", "float", "int", "int"]
    programName = input("Enter Name of the Program: ")
    print("Program Created")
    while True:
        add = input("Add to program? (Y/N): ").upper()
        if add == "Y":
            exercise = [programName, "Name", 0, 0.0, 0, 0]
            for i in range(1, len(para)):
                message = f"Enter {para[i]} as a {paraTyoe[i]}: "
                exercise[i] = checkType(input(message), paraTyoe[i], message, exercise[4])
            program.append(exercise)

        elif add == "N":
            break
        else:
            print("Invalid Input")

    return program

def runProgram(program: list, tracker: list) -> list:
    """
    Takes the program given, and then lets you enter your results into the tracker
    :param program: the exercise program
    :param tracker: history of exercises
    :return: updated tracker
    """
    print("Program Running")
    while True:
        add = input("Enter Date Manually? (Y/N): ").upper()
        if add == "Y":
            formatDate = input("Date (DD/MM/YYYY): ")
            break
        elif add == "N":
            today = date.today()
            formatDate = today.strftime("%m/%d/%Y")
            print(f"Date is {formatDate}")
            break
        else:
            print("Invalid Input")

    for i in range(len(program)):
        print(f"Time for {program[i][1]}.")
        print(f"This will be {program[i][2]} sets, each set being {program[i][4]} "
              f"to {program[i][5]} reps.")
        for j in range(program[i][2]):
            print(f"Set {j + 1}")
            tracker.append(addEntry(tracker, program[i][0], formatDate, program[i][1], j + 1,
                                    checkType(input("Enter weight: "), "float", "Enter weight: "),
                                    checkType(input("Enter reps: "), "int", "Enter reps: ")))

    return tracker

def addToProgram(program: str, exercise: str, numSets: int, incriment: float, min: int, max: int) -> list:
    return [program, exercise, numSets, incriment, min, max]

def printTracker(tracker):
    labels = ["Date", "Exercise Name", "Number of Sets", "Weight", "Rep Range", "1RM", "Diff"]
    for i in labels:
        print(i, end=" ")
    print()
    for i in range(len(tracker)):
        for j in range(len(tracker[i])):
            print(tracker[i][j], end=" ")
        print()

def addEntry(tracker: list, program: str, formatDate: str, name: str, setNum: int, weight: float, reps: int) -> list:
    max = round(weight * (1 + (float(reps) / 30)), 3)
    diff = 0
    for i in range(len(tracker) - 1, -1, -1):
        # print(tracker[i][1], tracker[i][2])
        if (tracker[i][0] == program) and (tracker[i][2] == name) and (tracker[i][3] == setNum):
            diff = max - tracker[i][5]

    return [program, formatDate, name, setNum, weight, reps, max, diff]

def makeList():
    return []

if __name__ == "__main__":
    tracker = []
    # tracker.append(addEntry(tracker, "1/1/20", "Bench", 1, 6, 200))
    # tracker.append(addEntry(tracker, "1/2/20", "Bench", 1, 7, 200))
    # tracker.append(addEntry(tracker, "1/3/20", "Bench", 1, 8, 200))
    # printTracker(tracker)
    print(runProgram(createProgram(), tracker))
