import sqlite3
from config import DB_FILENAME

db = sqlite3.connect(DB_FILENAME)
db.execute("PRAGMA foreign_keys = ON;")
