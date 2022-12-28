import os

TOKEN = os.environ["TOKEN"]
GUILD_ID = int(os.environ["GUILD_ID"])
DB_FILENAME = os.environ["DB_FILENAME"]
if DB_FILENAME == ":memory:":
    print("Warning: Running an in-memory database")

# discordId1,discordId2;discordId3,discordId4
incompatibilities = os.environ["INCOMPATIBILITIES"]
INCOMPATIBILITIES = []
if INCOMPATIBILITIES:
    for pair in incompatibilities.split(";"):
        a, b = map(int, pair.split(","))
        INCOMPATIBILITIES.append((a, b))
