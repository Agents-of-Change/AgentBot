from hack_path import hack_path

hack_path()
from db import db

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
