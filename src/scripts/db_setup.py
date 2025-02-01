from hack_path import hack_path
import sqlite3
from pathlib import Path
import dotenv
import os

dotenv.load_dotenv()

hack_path()
from db import db

db_path = Path(__file__).parent.parent / os.environ["DB_FILENAME"]
db = sqlite3.connect(db_path)

db.execute(
    """
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  discordId TEXT NOT NULL UNIQUE,
  matchable BOOLEAN NOT NULL
)
"""
)
db.execute(
    """
CREATE TABLE past_matches (
  id INTEGER PRIMARY KEY,
  date text default (strftime('%Y-%m-%d', 'now')),
  personA INTEGER NOT NULL,
  personB INTEGER NOT NULL,

  FOREIGN KEY (personA)
    REFERENCES users (id)
  FOREIGN KEY (personB)
    REFERENCES users (id)
)
"""
)

db.execute(
    """
CREATE TABLE timed_roles  (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    remove_role_at INTEGER NOT NULL,
    UNIQUE(user_id)
)
"""
)

db.execute(
    """
CREATE TABLE birthdays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    birthday DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
"""
)

db.commit()
db.close()
