import sqlite3
from config import DB_FILENAME
from pathlib import Path
import os

db_path = Path(__file__).parent / os.environ["DB_FILENAME"]
db = sqlite3.connect(db_path)
db.execute("PRAGMA foreign_keys = ON;")
