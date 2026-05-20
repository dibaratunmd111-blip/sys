# db.py – MySQL connection helper
# ─────────────────────────────────────────────────────────────
# Adjust HOST / USER / PASSWORD / DATABASE to match your setup.
# ─────────────────────────────────────────────────────────────

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",       # ← change if needed
    "password": "",           # ← change if needed
    "database": "inventory_db",
    "autocommit": True,
}


def get_connection():
    """Return a live MySQL connection or raise an Error."""
    return mysql.connector.connect(**DB_CONFIG)


def execute_query(sql: str, params: tuple = (), *, fetch: bool = False):
    """
    Run *sql* with *params*.
    - If fetch=True  → return list[dict]
    - If fetch=False → return lastrowid (int)
    Raises mysql.connector.Error on failure.
    """
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        if fetch:
            return cursor.fetchall()
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


# ─── Products ────────────────────────────────────────────────

def get_all_products():
    sql = """
        SELECT p.product_id, p.product_name, p.sku,
               c.category_name, s.supplier_name,
               p.quantity, p.unit_price, p.reorder_level,
               p.description, p.updated_at
        FROM   products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN suppliers  s ON p.supplier_id  = s.supplier_id
        ORDER BY p.product_name
    """
    return execute_query(sql, fetch=True)


def search_products(keyword: str):
    kw = f"%{keyword}%"
    sql = """
        SELECT p.product_id, p.product_name, p.sku,
               c.category_name, s.supplier_name,
               p.quantity, p.unit_price, p.reorder_level,
               p.description, p.updated_at
        FROM   products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN suppliers  s ON p.supplier_id  = s.supplier_id
        WHERE  p.product_name LIKE %s OR p.sku LIKE %s
               OR c.category_name LIKE %s
        ORDER BY p.product_name
    """
    return execute_query(sql, (kw, kw, kw), fetch=True)


def get_low_stock_products():
    sql = """
        SELECT p.product_id, p.product_name, p.sku,
               c.category_name, p.quantity, p.reorder_level
        FROM   products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE  p.quantity <= p.reorder_level
        ORDER BY p.quantity
    """
    return execute_query(sql, fetch=True)


def insert_product(data: dict) -> int:
    sql = """
        INSERT INTO products
            (product_name, sku, category_id, supplier_id,
             quantity, unit_price, reorder_level, description)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """
    return execute_query(sql, (
        data["product_name"], data["sku"],
        data["category_id"],  data["supplier_id"],
        data["quantity"],     data["unit_price"],
        data["reorder_level"],data["description"],
    ))


def update_product(product_id: int, data: dict):
    sql = """
        UPDATE products SET
            product_name  = %s, sku          = %s,
            category_id   = %s, supplier_id  = %s,
            quantity      = %s, unit_price   = %s,
            reorder_level = %s, description  = %s
        WHERE product_id = %s
    """
    execute_query(sql, (
        data["product_name"], data["sku"],
        data["category_id"],  data["supplier_id"],
        data["quantity"],     data["unit_price"],
        data["reorder_level"],data["description"],
        product_id,
    ))


def delete_product(product_id: int):
    execute_query("DELETE FROM products WHERE product_id = %s", (product_id,))


# ─── Stock Transactions ──────────────────────────────────────

def log_transaction(product_id: int, tx_type: str, qty: int, notes: str = ""):
    sql = """
        INSERT INTO stock_transactions
            (product_id, transaction_type, quantity_change, notes)
        VALUES (%s,%s,%s,%s)
    """
    execute_query(sql, (product_id, tx_type, qty, notes))


def adjust_stock(product_id: int, delta: int, tx_type: str, notes: str = ""):
    sql = "UPDATE products SET quantity = quantity + %s WHERE product_id = %s"
    execute_query(sql, (delta, product_id))
    log_transaction(product_id, tx_type, delta, notes)


def get_transactions(product_id: int = None):
    if product_id:
        sql = """
            SELECT t.transaction_id, p.product_name, t.transaction_type,
                   t.quantity_change, t.notes, t.transaction_date
            FROM   stock_transactions t
            JOIN   products p ON t.product_id = p.product_id
            WHERE  t.product_id = %s
            ORDER BY t.transaction_date DESC LIMIT 200
        """
        return execute_query(sql, (product_id,), fetch=True)
    sql = """
        SELECT t.transaction_id, p.product_name, t.transaction_type,
               t.quantity_change, t.notes, t.transaction_date
        FROM   stock_transactions t
        JOIN   products p ON t.product_id = p.product_id
        ORDER BY t.transaction_date DESC LIMIT 200
    """
    return execute_query(sql, fetch=True)


# ─── Categories & Suppliers ──────────────────────────────────

def get_categories():
    return execute_query("SELECT * FROM categories ORDER BY category_name", fetch=True)


def insert_category(name: str, desc: str = ""):
    execute_query(
        "INSERT INTO categories (category_name, description) VALUES (%s,%s)",
        (name, desc),
    )


def delete_category(cat_id: int):
    execute_query("DELETE FROM categories WHERE category_id = %s", (cat_id,))


def get_suppliers():
    return execute_query("SELECT * FROM suppliers ORDER BY supplier_name", fetch=True)


def insert_supplier(data: dict):
    sql = """
        INSERT INTO suppliers
            (supplier_name, contact_name, phone, email, address)
        VALUES (%s,%s,%s,%s,%s)
    """
    execute_query(sql, (
        data["supplier_name"], data["contact_name"],
        data["phone"], data["email"], data["address"],
    ))


def delete_supplier(sup_id: int):
    execute_query("DELETE FROM suppliers WHERE supplier_id = %s", (sup_id,))


# ─── Dashboard Summary ───────────────────────────────────────

def get_dashboard_stats() -> dict:
    rows = execute_query("SELECT COUNT(*) AS cnt FROM products", fetch=True)
    total_products = rows[0]["cnt"] if rows else 0

    rows = execute_query(
        "SELECT COUNT(*) AS cnt FROM products WHERE quantity <= reorder_level",
        fetch=True,
    )
    low_stock = rows[0]["cnt"] if rows else 0

    rows = execute_query(
        "SELECT COALESCE(SUM(quantity * unit_price), 0) AS val FROM products",
        fetch=True,
    )
    inventory_value = float(rows[0]["val"]) if rows else 0.0

    rows = execute_query(
        "SELECT COUNT(*) AS cnt FROM stock_transactions "
        "WHERE DATE(transaction_date) = CURDATE()",
        fetch=True,
    )
    today_tx = rows[0]["cnt"] if rows else 0

    return {
        "total_products":  total_products,
        "low_stock":       low_stock,
        "inventory_value": inventory_value,
        "today_tx":        today_tx,
    }
