import sqlite3,json

class OngoingGame:
    def __init__(self, db_file):
        self.db_file = db_file
        self.create_table()

    def create_table(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS games (
                                game_id TEXT PRIMARY KEY,
                                user_id TEXT,
                                username TEXT,
                                bet_amount REAL
                            )''')

    def check_user_exists(self, user_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT EXISTS (SELECT 1 FROM games WHERE user_id = ?) AS user_exists", (user_id,))
            result = cursor.fetchone()
            user_exists = result[0] == 1
            return user_exists

    def add_game(self, game_id, user_id, username, bet_amount):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''INSERT INTO games (game_id, user_id, username, bet_amount)
                                VALUES (?, ?, ?, ?)''', (game_id, user_id, username, bet_amount))
                return True
            except sqlite3.Error:
                return False

    def check_game_exists(self, game_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT EXISTS (SELECT 1 FROM games WHERE game_id = ?) AS game_exists", (game_id,))
            result = cursor.fetchone()
            game_exists = result[0] == 1
            return game_exists

    def remove_game(self, game_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''DELETE FROM games WHERE game_id = ?''', (game_id,))
            return cursor.rowcount > 0

    def get_all_games_as_json(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM games")
            rows = cursor.fetchall()
            if not rows:
                return False
            games = [{'game_id': row[0], 'user_id': row[1], 'username': row[2], 'bet_amount': row[3]} for row in rows]
            return json.dumps(games)

