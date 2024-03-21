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
            cursor.execute('''CREATE TABLE IF NOT EXISTS dice (
                                game_id TEXT PRIMARY KEY,
                                user_id INTEGER,
                                username TEXT,
                                bet_amount REAL,
                                bot_round_1 INTEGER,
                                bot_round_2 INTEGER,
                                bot_round_3 INTEGER,
                                bot_round_4 INTEGER,
                                bot_round_5 INTEGER,
                                user_round_1 INTEGER,
                                user_round_2 INTEGER,
                                user_round_3 INTEGER,
                                user_round_4 INTEGER,
                                user_round_5 INTEGER,
                                user_score INTEGER DEFAULT 0,
                                bot_score INTEGER DEFAULT 0,
                                winner TEXT
                            )''')

    def add_ids(self, game_id, user_id, username, bet_amount):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO dice (game_id, user_id, username, bet_amount)
                              VALUES (?, ?, ?, ?)''', (game_id, user_id, username, bet_amount))

    def add_round(self, game_id, round_type, round_value, diceval):
        round_column = f"{round_type}_round_{round_value}"
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE dice SET {round_column} = ? WHERE game_id = ?", (diceval, game_id))

    def add_winner(self, game_id, winner):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE dice SET winner = ? WHERE game_id = ?", (winner, game_id))

    def enter_bot_score(self, game_id, bot_score):
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''UPDATE dice
                                  SET bot_score = ?
                                  WHERE game_id = ?''', (bot_score, game_id))

    def enter_user_score(self, game_id, user_score):
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''UPDATE dice
                                  SET user_score = ?
                                  WHERE game_id = ?''', (user_score, game_id))

    def get_round_value(self, game_id, round_type, round_value):
        round_column = f"{round_type}_round_{round_value}"
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT {round_column} FROM dice WHERE game_id = ?", (game_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None

    def get_scores(self, game_id):
            with sqlite3.connect(self.db_file) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''SELECT bot_score, user_score
                                      FROM dice
                                      WHERE game_id = ?''', (game_id,))
                    return cursor.fetchone()
    def get_bet(self,game_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT bet_amount FROM dice WHERE game_id = ?''',(game_id,))
            return cursor.fetchone()
