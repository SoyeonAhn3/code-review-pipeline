import sqlite3

conn = sqlite3.connect("shop.db")


def get_all_orders():
    users = conn.execute("SELECT * FROM users").fetchall()
    result = []
    for user in users:
        orders = conn.execute(
            f"SELECT * FROM orders WHERE user_id = {user[0]}"
        ).fetchall()
        for order in orders:
            items = conn.execute(
                f"SELECT * FROM items WHERE order_id = {order[0]}"
            ).fetchall()
            result.append({"user": user, "order": order, "items": items})
    return result


def get_expensive_products(min_price):
    all_products = conn.execute("SELECT * FROM products").fetchall()
    return [p for p in all_products if p[2] > min_price]
