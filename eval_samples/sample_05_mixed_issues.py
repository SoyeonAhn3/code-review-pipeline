import sqlite3
import pickle
import os

conn = sqlite3.connect("app.db")
API_KEY = "sk-proj-abc123xyz789"


def search_users(name):
    q = f"SELECT * FROM users WHERE name LIKE '%{name}%'"
    return conn.execute(q).fetchall()


def load_user_data(filepath):
    with open(filepath, "rb") as f:
        return pickle.load(f)


def get_user_orders(user_ids):
    results = []
    for uid in user_ids:
        orders = conn.execute(
            f"SELECT * FROM orders WHERE uid = {uid}"
        ).fetchall()
        results.append(orders)
    return results


def process(data):
    out = []
    for d in data:
        try:
            v = d["value"] / d["count"]
            out.append(v)
        except:
            pass
    return out


def run_command(cmd):
    os.system(cmd)
