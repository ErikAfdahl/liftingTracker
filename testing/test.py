import random
prd = ["bench", "incline bench"] # new prs in
exercises = ["bench", "incline bench", "ohp", "tricep pushdowns"] # total number of exercises
declined = ["ohp"] # exercises that declined compared to last time
stagnant = ["tricep pushdowns"]
improved = ["bench", "incline bench"]
highlight = "incline bench"
heaviest = "bench"
numQuality = 1 - (len(declined) / len(exercises)) + (len(improved) / len(exercises))
quality = "poor"
program = "push"
lastDate = "1/1/26"
if numQuality >= .75:
    quality = "excellent"
elif numQuality >= .5:
    quality = "good"
elif numQuality >= .25:
    quality = "okay"

excellent = [
    "a marked",
    "a substantial",
    "a significant",
    "a considerable",
    "a notable",
]

good = [
    "a clear",
    "a meaningful",
    "a visible",
    "a distinct",
    "a measurable",
]

okay = [
    "some",
    "a moderate",
    "a partial",
    "a mild",
    "a slight",
]

poor = [
    "a minor",
    "a marginal",
    "a negligible",
    "a barely noticeable",
    "a trivial",
]

bad = [
    "an imperceptible",
    "a questionable",
    "a dubious",
    "a supposed",
    "an alleged",
]
report = ""

if (len(prd) / len(exercises)) >= .8:
    report += f"Just want to say, today was {random.choice(excellent)} day, with you setting new PR's in {len(prd)} exercises."
elif (len(prd) / len(exercises)) >= .6:
    report += f"First of all, today was {random.choice(good)} day, with you setting new PR's in {len(prd)} exercises."
elif (len(prd) / len(exercises)) > 0:
    report += f"Before anything else, good work on the new PR's!"

if len(report) > 0:
    report += f" But over all today was a {quality} day, today's {program} program's highlight was {highlight} and {heaviest} was your heaviest exercise using {heaviest} pounds. "
else:
    report += f"Over all today was a {quality} day, today's {program} program's highlight was {highlight} and {heaviest} was your heaviest exercise using {heaviest} pounds. "

if len(declined) > 0:
    report += "There was"
    if (len(declined) / len(exercises)) >= .8:
        report += random.choice(excellent)
    elif (len(declined) / len(exercises)) >= .6:
        report += random.choice(good)
    elif (len(declined) / len(exercises)) >= .4:
        report += random.choice(okay)
    elif (len(declined) / len(exercises)) >= .2:
        report += random.choice(poor)
    else:
        report += random.choice(bad)

    if len(declined) == 1:
        report += (f" amount of regression compared to {lastDate}, as 1 "
                   f"exercise declined in that first set, out of {len(exercises)} total exercises, only {declined[0]} regressed.")
    elif len(declined) == 2:
        report += (f" amount of regression compared to {lastDate}, as 2 "
                   f"exercises declined in that first set, out of {len(exercises)} total exercises, "
                   f"{declined[0]} and {declined[1]} we're the only exercises who regressed.")
    else:
        report += (f" amount of regression compared to {lastDate}, as {len(declined)} "
                   f"exercises declined in that first set, out of {len(exercises)} total exercises. The exercises that regressed are;")
        for i in range(len(declined)):
            if i == 0:
                report += f" {declined[i]}"
            elif i == len(declined) - 1:
                report += f", and {declined[i]}."
            else:
                report += f", {declined[i]}"

if len(stagnant) > 0:
    if len(declined) > 0:
        report += " There was also"
    else:
        report += " There was"

    if (len(stagnant) / len(exercises)) >= .8:
        report += random.choice(excellent)
    elif (len(stagnant) / len(exercises)) >= .6:
        report += random.choice(good)
    elif (len(stagnant) / len(exercises)) >= .4:
        report += random.choice(okay)
    elif (len(stagnant) / len(exercises)) >= .2:
        report += random.choice(poor)
    else:
        report += random.choice(bad)

    if len(stagnant) == 1:
        report += (f" amount of stagnation compared to {lastDate}, as 1 "
                   f"exercise were stagnant in that first set, out of {len(exercises)} exercises, only {stagnant[0]} stagnated.")
    elif len(stagnant) == 2:
        report += (f" amount of stagnation compared to {lastDate}, as 2 "
                   f"exercises were stagnant in that first set, out of {len(exercises)} exercises, "
                   f"{stagnant[0]} and {stagnant[1]} we're the only exercises who stagnated.")
    else:
        report += (f" amount of stagnation compared to {lastDate}, as {len(stagnant)} "
                   f"exercises were stagnant in that first set, out of {len(exercises)} exercises. The exercises that stagnated are;")
        for i in range(len(stagnant)):
            if i == 0:
                report += f" {stagnant[i]}"
            elif i == len(stagnant) - 1:
                report += f", and {stagnant[i]}."
            else:
                report += f", {stagnant[i]}"

if len(improved) > 0:
    if (len(declined) > 0) and (len(stagnant) > 0):
        report += " However there"
    elif len(declined) > 0:
        report += " But there was also"
    elif len(stagnant) > 0:
        report += " And there was also"
    else:
        report += " There"

    if (len(improved) / len(exercises)) >= .8:
        report += random.choice(excellent)
    elif (len(improved) / len(exercises)) >= .6:
        report += random.choice(good)
    elif (len(improved) / len(exercises)) >= .4:
        report += random.choice(okay)
    elif (len(improved) / len(exercises)) >= .2:
        report += random.choice(poor)
    else:
        report += random.choice(bad)

    if len(improved) == 1:
        report += (f" amount of improvement compared to {lastDate}, as 1 "
                   f"exercise improved in that first set, out of {len(exercises)} exercises, only {improved[0]} improved.")
    elif len(improved) == 2:
        report += (f" amount of improvement compared to {lastDate}, as 2 "
                   f"exercises improved in that first set, out of {len(exercises)} exercises, "
                   f"{improved[0]} and {improved[1]} we're the only exercises who improved.")
    else:
        report += (f" amount of improvement compared to {lastDate}, as {len(improved)} "
                   f"exercises improved in that first set, out of {len(exercises)} exercises. The exercises that improved are;")
        for i in range(len(improved)):
            if i == 0:
                report += f" {improved[i]}"
            elif i == len(improved) - 1:
                report += f", and {improved[i]}."
            else:
                report += f", {improved[i]}"

if numQuality >= .75:
    report += " Keep up the great work!"
elif numQuality >= .5:
    report += " But good job today overall."
elif numQuality >= .25:
    report += " As long as you tried you're all good."
else:
    report += " But get some rest and be ready for next time."
print(report)