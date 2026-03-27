import sqlite3

DB_PASSWORD = "super_secret_123"
conn = sqlite3.connect("production.db")


def get_user(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor = conn.execute(query)
    return cursor.fetchone()


def authenticate(username, password):
    if password == DB_PASSWORD:
        user = get_user(username)
        return user
    return None


def delete_user(user_id):
    conn.execute(f"DELETE FROM users WHERE id = {user_id}")
    conn.commit()
