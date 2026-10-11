def check_ranges1(min, max):
    if (not min) or (not max):
        print(f"1: {min}, {max}")
        return False
    elif (min[-1] == ",") or (max[-1] == ","):
        print(f"2: {min[-1]}, {max[-1]}")
        return False
    else:
        for i in range(len(min)):
            if (not min[i].isdigit()) and (min[i] != ","):
                print(f"3: {min[i]}")
                return False

        for i in range(len(max)):
            if (not max[i].isdigit()) and (max[i] != ","):
                print(f"3: {max[i]}")
                return False

    return True

def parseRepRange(repRange, numSets):
    try:
        parts = [int(x.strip()) for x in str(repRange).split(",")]

        if len(parts) >= numSets:
            return parts[:numSets]
        else:
            return parts + [parts[-1]] * (numSets - len(parts))
    except ValueError:
        return []

def check_ranges2(min, max):
    if len(min) != 0 and len(max) != 0:
        for i in range(len(min)):
            if min[i] > max[i]:
                return False
    return True

if __name__ == "__main__":
    sets = 4
    min = "1, 2, 3, 4".replace(" ", "")
    max = "2, 3, 2".replace(" ", "")
    if check_ranges1(min, max):
        min = parseRepRange(min, sets)
        max = parseRepRange(max, sets)
        print("passed1")
        if check_ranges2(min, max):
            print("passed2")
        else:
            print("failed2")
    else:
        print("failed1")
    print(min)
    print(max)

    # after this passes, check values to make sure all mins are less than maxes, and make sure the lists arent larger than the sets