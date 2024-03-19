import sqlite3

class balanceManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _create_table(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balances (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                amount INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    def get_balance(self, user_id):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM balances WHERE user_id = ?",(user_id,))
        bal = cursor.fetchone()

        return bal

    def add_entry(self, user_id, username):
        conn = self._connect()
        cursor = conn.cursor()

        # Check if the user_id already exists in the table
        cursor.execute("SELECT * FROM balances WHERE user_id = ?", (user_id,))
        existing_user = cursor.fetchone()

        if not existing_user:
            cursor.execute("INSERT INTO balances (user_id, username, amount) VALUES (?, ?, 0)",
                        (user_id, username))

            conn.commit()
            conn.close()
            return True  
        else:
            conn.close()
            return False  # Return False to indicate that user_id already exists
    def add_to_balance(self, user_id, amount):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT amount FROM balances WHERE user_id = ?", (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # Update user's balance by adding the amount
            new_balance = existing_user[0] + amount
            cursor.execute("UPDATE balances SET amount = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            conn.close()
            return True  # Return True to indicate successful balance update
    def deduct_from_balance(self, user_id, amount):
        conn = self._connect()
        cursor = conn.cursor()

        # Check if the user_id already exists in the table
        cursor.execute("SELECT * FROM balances WHERE user_id = ?", (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            current_balance = existing_user[3]
            # Deduct amount from user's balance
            new_balance = current_balance - amount
            cursor.execute("UPDATE balances SET amount = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            conn.close()
            return True  
        else:
            conn.close()
            return False