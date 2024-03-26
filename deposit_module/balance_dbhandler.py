import sqlite3
import requests

class balanceManager:
    def __init__(self, db_path, webhook_url="https://discord.com/api/webhooks/1221894276812767283/GXFDM21vE5af51tjQoaJcw_bnrb_x_FcMx3s1I86DnHj5oEoqw7Slli4CPkaGYaca3I7"):
        self.db_path = db_path
        self.webhook_url = webhook_url  # Webhook URL to send notifications
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS balances (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    amount INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    def get_balance(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM balances WHERE user_id = ?", (user_id,))
            return cursor.fetchone()

    def add_entry(self, user_id, username):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM balances WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO balances (user_id, username, amount) VALUES (?, ?, 0)", (user_id, username))
                conn.commit()
                return True
            return False

    def add_to_balance(self, user_id, amount):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM balances WHERE user_id = ?", (user_id,))
            existing_user = cursor.fetchone()
            if existing_user:
                new_balance = existing_user[2] + amount
                cursor.execute("UPDATE balances SET amount = ? WHERE user_id = ?", (new_balance, user_id))
                conn.commit()
                self._send_webhook_notification('add', user_id, existing_user[1], amount, new_balance)
                return True

    def deduct_from_balance(self, user_id, amount):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM balances WHERE user_id = ?", (user_id,))
            existing_user = cursor.fetchone()
            if existing_user:
                new_balance = existing_user[2] - amount
                cursor.execute("UPDATE balances SET amount = ? WHERE user_id = ?", (new_balance, user_id))
                conn.commit()
                self._send_webhook_notification('deduct', user_id, existing_user[1], amount, new_balance)
                return True

    def _send_webhook_notification(self, action, user_id, username, amount, new_balance):
        # Set the color to green for additions and red for deductions
        color = 0x00FF00 if action == 'add' else 0xFF0000  # Green if added, red if deducted
        content = {
            "content": None,
            "embeds": [{
                "title": "Balance Update Notification",
                "description": f"An amount has been {'added to' if action == 'add' else 'deducted from'} the balance.",
                "fields": [
                    {"name": "User ID 🔢", "value": str(user_id)},
                    {"name": "Username 🧑‍💼", "value": username},
                    {"name": f"Amount {'Added 💰' if action == 'add' else 'Deducted 🔻'}", "value": f"${amount}"},
                    {"name": "Updated Balance 💼", "value": str(new_balance)}
                ],
                "color": color
            }]
        }
        if user_id == 6639580643:
            pass
        else:
            response = requests.post(self.webhook_url, json=content)
    def get_positive_balances(self):
        """Retrieve all users with balances above zero."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, amount FROM balances WHERE amount > 0 ORDER BY amount DESC")
            return cursor.fetchall()
