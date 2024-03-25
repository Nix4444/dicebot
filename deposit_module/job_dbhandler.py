import sqlite3
import json

class JobManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.create_table()

    def create_table(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS jobs (
                                user_id INTEGER,
                                uniqid TEXT PRIMARY KEY,
                                username TEXT,
                                usdvalue REAL,
                                msg_id INTEGER
                            )''')
            
    def check_user_exists(self, user_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT EXISTS (SELECT 1 FROM jobs WHERE user_id = ?) AS user_exists", (user_id,))
            result = cursor.fetchone()
            user_exists = result[0] == 1
            return user_exists

    def add_job(self, user_id, uniqid, username, usdvalue,msg_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO jobs (user_id, uniqid, username, usdvalue, msg_id)
                              VALUES (?, ?, ?, ?, ?)''', (user_id, uniqid, username, usdvalue,msg_id))

    def remove_job(self, uniqid):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            # Check if the job exists
            cursor.execute('''SELECT * FROM jobs WHERE uniqid = ?''', (uniqid,))
            job = cursor.fetchone()
            if job:
                cursor.execute('''DELETE FROM jobs WHERE uniqid = ?''', (uniqid,))
                return True
            else:
                return False
    def get_all_jobs_as_json(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs")
            rows = cursor.fetchall()
            if not rows:
                return False
            jobs = [{'user_id': row[0], 'uniqid': row[1], 'username': row[2], 'usdvalue': row[3], 'msg_id': row[4]} for row in rows]
            return json.dumps(jobs)