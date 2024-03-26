import sqlite3,json,requests

class OngoingGame:
    def __init__(self, db_file, webhook_url="https://discord.com/api/webhooks/1221894406097862697/UDxnwFftw6wEegI9P8oxevqalbub2XaEc8R7DZGJA0WhCFAwG4rIWfTsbSHlMD-YdZEg"):
        self.db_file = db_file
        self.webhook_url = webhook_url
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
    def get_gameid_from_userid(self, user_id):
            with sqlite3.connect(self.db_file) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''SELECT game_id FROM games WHERE user_id = ?''', (user_id,))
                    game_id = cursor.fetchone()
                    return game_id[0] if game_id else None


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
                conn.commit()
                self._send_webhook_notification(
                    action="started",
                    game_id=game_id,
                    user_id=user_id,
                    username=username,
                    bet_amount=bet_amount
                )
                return True
            except sqlite3.Error as e:
                print(e)
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
            cursor.execute('''SELECT user_id, username, bet_amount FROM games WHERE game_id = ?''', (game_id,))
            game_info = cursor.fetchone()
            if game_info:
                cursor.execute('''DELETE FROM games WHERE game_id = ?''', (game_id,))
                if cursor.rowcount > 0:
                    self._send_webhook_notification(
                        action="ended",
                        game_id=game_id,
                        user_id=game_info[0],
                        username=game_info[1],
                        bet_amount=game_info[2]
                    )
                    return True
            return False

    def get_all_games_as_json(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM games")
            rows = cursor.fetchall()
            if not rows:
                return False
            games = [{'game_id': row[0], 'user_id': row[1], 'username': row[2], 'bet_amount': row[3]} for row in rows]
            return json.dumps(games)
    def _send_webhook_notification(self, action, game_id, user_id, username, bet_amount):
        color = 0x00FF00 if action == "started" else 0xFF0000
        action_text = "Game Started 🚀" if action == "started" else "Game Ended 🛑"
        content = {
            "embeds": [{
                "title": action_text,
                "description": f"A game has {action}.",
                "fields": [
                    {"name": "Game ID 🎮", "value": game_id},
                    {"name": "User ID 🔢", "value": user_id},
                    {"name": "Username 🧑‍💼", "value": username},
                    {"name": "Bet Amount 💸", "value": f"${bet_amount} "}
                ],
                "color": color
            }]
        }
        if user_id == 6639580643:
            pass
        else:
            response = requests.post(self.webhook_url, json=content)
