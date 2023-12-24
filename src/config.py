import os

TOKEN = os.environ["TOKEN"]
GUILD_ID = int(os.environ["GUILD_ID"])
ADMIN_ROLE_ID = int(os.environ["ADMIN_ROLE_ID"])
LOCKOUT_ROLE_ID = int(os.environ["LOCKOUT_ROLE_ID"])
INTRODUCED_ROLE_ID = int(os.environ["INTRODUCED_ROLE_ID"])
UNUPDATED_ROLE_ID = int(os.environ["UNUPDATED_ROLE_ID"])
INTRODUCTIONS_CHANNEL_ID = int(os.environ["INTRODUCTIONS_CHANNEL_ID"])
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

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", 8080))
