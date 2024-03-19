import sqlite3

class orderManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                uniqid TEXT PRIMARY KEY,
                user_id INTEGER,
                username TEXT,
                status TEXT,
                crypto TEXT,
                amount INTEGER,
                hash TEXT,
                coin_amount REAL,
                address TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def insert_order(self, user_id, username, uniqid, status, crypto, usdvalue, hash, amount, address):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (user_id, username, uniqid, status, crypto, amount, hash, coin_amount, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, uniqid, status, crypto, usdvalue, hash,amount , address))
        conn.commit()
        conn.close()

    def update_order_status(self, uniqid, new_status):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders SET status = ? WHERE uniqid = ?
        ''', (new_status, uniqid))
        conn.commit()
        conn.close()

    def get_order_status(self, uniqid):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM orders WHERE uniqid = ?', (uniqid,))
        status = cursor.fetchone()
        conn.close()
        return status[0] if status else None

    def get_order_details(self, uniqid):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE uniqid = ?', (uniqid,))
        details = cursor.fetchone()
        conn.close()
        return details

    def update_order_hash(self, uniqid, crypto_hash):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders SET hash = ? WHERE uniqid = ?
        ''', (crypto_hash, uniqid))
        conn.commit()
        conn.close()

    def get_order_by_uniqid(self, uniqid):
        conn = self._connect()
        cursor = conn.cursor()

        # Execute the query to fetch data for the given uniqid
        cursor.execute('''
            SELECT crypto, coin_amount, address, amount
            FROM orders
            WHERE uniqid = ?
        ''', (uniqid,))

        # Fetch the row from the result set
        order_data = cursor.fetchone()

        conn.close()

        return order_data
