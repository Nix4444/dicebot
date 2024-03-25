import sqlite3
import random
import string
import requests
class WithdrawalData:
    def __init__(self, db_name):
        self.db_name = db_name
        self.webhook_url = "https://discord.com/api/webhooks/1221894122848125129/7aSXxgI58XCdtdxMoeCCDCGZJmKofZrd6m_bBdbXvlXHM6OCuLUJvSIJlaQKqtcK84cb"
        self.create_withdrawal_table()

    def create_withdrawal_table(self):
        """Create a withdrawal table"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS withdrawals (
                    withdrawalid TEXT PRIMARY KEY,
                    userid INTEGER,
                    username TEXT,
                    amount INTEGER,
                    coin TEXT,
                    address TEXT,
                    hash TEXT
                )
            ''')
            conn.commit()

    def generate_random_string(self, length):
        """Generate a random string of fixed length"""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def insert_withdrawal(self, userid, username, amount, coin, address, hash_value):
        """Insert withdrawal data into the table and send Discord notification"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            withdrawalid = self.generate_random_string(12)  # Generate a random withdrawal ID
            cursor.execute('''
                INSERT INTO withdrawals (withdrawalid, userid, username, amount, coin, address, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (withdrawalid, userid, username, amount, coin, address, hash_value))
            conn.commit()

        color_code = "#39d113"
        color_int = int(color_code.strip("#"), 16)
        embed_content = {
            "embeds": [
                {
                    "title": "Withdrawal Successful",
                    "fields": [
                        {"name": "Withdrawal ID 🆔", "value": withdrawalid},
                        {"name": "User ID 🔢", "value": str(userid)},
                        {"name": "Username 🧑", "value": username},
                        {"name": "Amount 💰", "value": f"${amount}"},
                        {"name": "Address 🏠", "value": address},
                        {"name": "Hash 📦", "value": hash_value},
                    ],
                    "color": color_int  # You can change this to any color you like
                }
            ]
        }
        response = requests.post(self.webhook_url, json=embed_content)

    def get_withdrawals_by_userid(self, userid):
        """Retrieve withdrawals by user ID"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM withdrawals WHERE userid = ?
            ''', (userid,))
            withdrawals = cursor.fetchall()
            return withdrawals
