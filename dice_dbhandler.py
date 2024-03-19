import sqlite3
import random
import string

class DiceManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.create_table()

    def create_table(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS games (
                                game_id TEXT PRIMARY KEY,
                                user_id INTEGER,
                                username TEXT,
                                bet_amount REAL,
                                bot_round_1 INTEGER,
                                bot_round_2 INTEGER,
                                bot_round_3 INTEGER,
                                user_round_1 INTEGER,
                                user_round_2 INTEGER,
                                user_round_3 INTEGER,
                                winner TEXT
                            )''')

    def add_ids(self, game_id, user_id, username, bet_amount):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO games (game_id, user_id, username, bet_amount)
                              VALUES (?, ?, ?, ?)''', (game_id, user_id, username, bet_amount))

    def add_round(self, game_id, round_type, round_value):
        round_column = f"{round_type}_round_{round_value}"
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE games SET {round_column} = ? WHERE game_id = ?", (round_value, game_id))

    def add_winner(self, game_id, winner):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE games SET winner = ? WHERE game_id = ?", (winner, game_id))