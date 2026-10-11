from datetime import *

# randomDate = "2026-09-18"

today = datetime.strptime("2026-10-18", "%Y-%m-%d")
randomDate = datetime.strptime("2026-09-18", "%Y-%m-%d")
print((today - randomDate).days)