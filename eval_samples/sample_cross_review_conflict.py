# 의도적으로 보안↔성능 충돌이 나는 샘플 코드
# Security: SQL Injection + 입력 검증 누락
# Performance: 루프 안에서 DB 호출 (N+1) + 보안 수정이 루프 안에 들어가면 성능 저하
# Quality: 매직 넘버 + 네이밍

import sqlite3

db = sqlite3.connect("app.db")
PASSWORD = "admin1234"


def get_users(role):
    query = f"SELECT * FROM users WHERE role = '{role}'"
    cursor = db.execute(query)
    return cursor.fetchall()


def process_orders(user_ids):
    results = []
    for uid in user_ids:
        # N+1: 루프 안에서 매번 DB 호출
        order = db.execute(f"SELECT * FROM orders WHERE user_id = {uid}").fetchall()
        for o in order:
            if o[3] > 1000:  # 매직 넘버
                results.append(o)
    return results


def login(username, pw):
    if pw == PASSWORD:
        q = f"SELECT * FROM users WHERE name = '{username}'"
        user = db.execute(q).fetchone()
        return user
    return None
