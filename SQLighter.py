import sqlite3


class SQLighter:

    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file)
        self.cursor = self.connection.cursor()

    def get_grades_for_chat(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT grades FROM subscriptions WHERE user_id = ?", (user_id,)).fetchone()
            return result[0]

    def subscriber_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)).fetchall()
            return bool(len(result))

    def get_all_chats_info(self, status=True):
        with self.connection:
            return self.cursor.execute("SELECT user_id, username, password FROM subscriptions WHERE status = ?",
                                       (status,)).fetchall()

    def save_grades(self, username, grades):
        self.cursor.execute("UPDATE subscriptions SET grades = ? WHERE username = ?", (grades, username))
        self.connection.commit()

    def add_subscriber(self, user_id, status=False):
        with self.connection:
            return self.cursor.execute("INSERT INTO subscriptions ('status', 'user_id') VALUES (?,?)",
                                       (status, user_id))

    def update_subscription(self, user_id, status):
        self.connection.commit()
        return self.cursor.execute("UPDATE subscriptions SET status = ? WHERE user_id = ?", (status, user_id))

    def get_subscription(self, user_id):
        result = self.cursor.execute("SELECT status FROM subscriptions WHERE user_id = ?", (user_id,)).fetchone()
        return result[0]

    def update_username(self, user_id, username):
        self.cursor.execute("UPDATE subscriptions SET username = ? WHERE user_id = ?", (username, user_id))
        self.connection.commit()

    def update_password(self, user_id, password):
        self.cursor.execute("UPDATE subscriptions SET password = ? WHERE user_id = ?", (password, user_id))
        self.connection.commit()

    def get_username(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT username FROM subscriptions WHERE user_id = ?", (user_id,)).fetchone()
            return result[0]

    def get_password(self, user_id):
        with self.connection:
            result = self.cursor.execute('SELECT password FROM subscriptions WHERE user_id = ?', (user_id,)).fetchone()
            return result[0]

    def close(self):
        self.connection.close()
