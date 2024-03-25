import sqlite3

class WithdrawalState:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_table()

    def create_table(self):
        """Creates the isWithdrawing table if it doesn't already exist."""
        with sqlite3.connect(self.db_path) as conn:
            query = '''CREATE TABLE IF NOT EXISTS isWithdrawing (
                        userid INTEGER PRIMARY KEY,
                        username TEXT NOT NULL
                       );'''
            conn.execute(query)

    def add_record(self, userid, username):
        """Adds a new record to the isWithdrawing table."""
        with sqlite3.connect(self.db_path) as conn:
            try:
                query = '''INSERT INTO isWithdrawing (userid, username)
                           VALUES (?, ?);'''
                conn.execute(query, (userid, username))
                conn.commit()
            except sqlite3.IntegrityError:
                print("Record already exists.")
            except sqlite3.Error as e:
                print(f"An error occurred: {e}")

    def remove_record(self, userid):
        """Removes a record from the isWithdrawing table."""
        with sqlite3.connect(self.db_path) as conn:
            query = '''DELETE FROM isWithdrawing WHERE userid = ?;'''
            cursor = conn.execute(query, (userid,))
            conn.commit()
            return cursor.rowcount > 0

    def user_exists(self, userid):
        """Checks if a user exists in the isWithdrawing table."""
        with sqlite3.connect(self.db_path) as conn:
            query = '''SELECT 1 FROM isWithdrawing WHERE userid = ?;'''
            cursor = conn.execute(query, (userid,))
            result = cursor.fetchone()
            return result is not None
        
    def clear_withdrawal_state(self):
        with sqlite3.connect(self.db_path) as conn:
            query = 'DELETE FROM isWithdrawing;'
            conn.execute(query)
            conn.commit()
