import os

TOKEN = os.environ["TOKEN"]
GUILD_ID = int(os.environ["GUILD_ID"])
DB_FILENAME = os.environ["DB_FILENAME"]
if DB_FILENAME == ":memory:":
    print("Warning: Running an in-memory database")
