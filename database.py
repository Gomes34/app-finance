import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.expanduser("~"), "financeapp_pro.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#5B8DEF',
            icon  TEXT DEFAULT '💰',
            type  TEXT DEFAULT 'expense'
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount      REAL NOT NULL,
            type        TEXT NOT NULL,
            category_id INTEGER,
            date        TEXT NOT NULL,
            notes       TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            amount      REAL NOT NULL,
            billing_day INTEGER NOT NULL,
            category_id INTEGER,
            active      INTEGER DEFAULT 1,
            start_date  TEXT,
            notes       TEXT,
            color       TEXT DEFAULT '#5B8DEF',
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        CREATE TABLE IF NOT EXISTS goals (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT NOT NULL,
            target_amount  REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            deadline       TEXT,
            color          TEXT DEFAULT '#5B8DEF',
            icon           TEXT DEFAULT '🎯',
            created_at     TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    defaults = [
        ("Alimentação",  "#FF6B6B", "🍔", "expense"),
        ("Transporte",   "#4ECDC4", "🚗", "expense"),
        ("Moradia",      "#45B7D1", "🏠", "expense"),
        ("Saúde",        "#96CEB4", "💊", "expense"),
        ("Lazer",        "#F7B731", "🎮", "expense"),
        ("Educação",     "#A29BFE", "📚", "expense"),
        ("Vestuário",    "#FD79A8", "👕", "expense"),
        ("Streaming",    "#6C63FF", "📺", "expense"),
        ("Mercado",      "#00B894", "🛒", "expense"),
        ("Outros",       "#B2BEC3", "📦", "expense"),
        ("Salário",      "#00B894", "💼", "income"),
        ("Freelance",    "#00CEC9", "💻", "income"),
        ("Investimentos","#FDCB6E", "📈", "income"),
        ("Outros Ganhos","#74B9FF", "💵", "income"),
    ]
    for row in defaults:
        c.execute(
            "INSERT OR IGNORE INTO categories (name,color,icon,type) VALUES (?,?,?,?)",
            row)
    conn.commit()
    conn.close()


# ── Transactions ─────────────────────────────────────────────────────────────

def add_transaction(description, amount, t_type, category_id, date, notes=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO transactions (description,amount,type,category_id,date,notes)"
        " VALUES (?,?,?,?,?,?)",
        (description, amount, t_type, category_id, date, notes))
    conn.commit(); conn.close()


def get_transactions(month=None, year=None, limit=None):
    conn = get_connection()
    q = """SELECT t.*,
                  c.name  AS category_name,
                  c.color AS category_color,
                  c.icon  AS category_icon
           FROM transactions t
           LEFT JOIN categories c ON t.category_id = c.id"""
    params = []
    if month and year:
        q += " WHERE strftime('%m',t.date)=? AND strftime('%Y',t.date)=?"
        params = [f"{month:02d}", str(year)]
    q += " ORDER BY t.date DESC, t.created_at DESC"
    if limit:
        q += f" LIMIT {limit}"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows


def delete_transaction(tid):
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
    conn.commit(); conn.close()


def update_transaction(tid, description, amount, t_type, category_id, date, notes):
    conn = get_connection()
    conn.execute(
        "UPDATE transactions SET description=?,amount=?,type=?,"
        "category_id=?,date=?,notes=? WHERE id=?",
        (description, amount, t_type, category_id, date, notes, tid))
    conn.commit(); conn.close()


def get_monthly_summary(year=None):
    conn = get_connection()
    year = year or datetime.now().year
    rows = conn.execute("""
        SELECT strftime('%m',date) AS month, type, SUM(amount) AS total
        FROM transactions
        WHERE strftime('%Y',date)=?
        GROUP BY month, type ORDER BY month
    """, (str(year),)).fetchall()
    conn.close()
    return rows


def get_category_breakdown(month, year):
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.name, c.color, c.icon, SUM(t.amount) AS total
        FROM transactions t
        JOIN categories c ON t.category_id=c.id
        WHERE strftime('%m',t.date)=? AND strftime('%Y',t.date)=?
          AND t.type='expense'
        GROUP BY c.id ORDER BY total DESC
    """, (f"{month:02d}", str(year))).fetchall()
    conn.close()
    return rows


# ── Categories ────────────────────────────────────────────────────────────────

def get_categories(cat_type=None):
    conn = get_connection()
    if cat_type:
        rows = conn.execute(
            "SELECT * FROM categories WHERE type=? ORDER BY name",
            (cat_type,)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return rows


# ── Subscriptions ─────────────────────────────────────────────────────────────

def add_subscription(name, amount, billing_day, category_id,
                     start_date, notes, color):
    conn = get_connection()
    conn.execute(
        "INSERT INTO subscriptions "
        "(name,amount,billing_day,category_id,start_date,notes,color)"
        " VALUES (?,?,?,?,?,?,?)",
        (name, amount, billing_day, category_id, start_date, notes, color))
    conn.commit(); conn.close()


def get_subscriptions():
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.*, c.name AS category_name, c.icon AS category_icon
        FROM subscriptions s
        LEFT JOIN categories c ON s.category_id=c.id
        ORDER BY s.name
    """).fetchall()
    conn.close()
    return rows


def toggle_subscription(sid):
    conn = get_connection()
    conn.execute(
        "UPDATE subscriptions SET active=CASE WHEN active=1 THEN 0 ELSE 1 END"
        " WHERE id=?", (sid,))
    conn.commit(); conn.close()


def delete_subscription(sid):
    conn = get_connection()
    conn.execute("DELETE FROM subscriptions WHERE id=?", (sid,))
    conn.commit(); conn.close()


def update_subscription(sid, name, amount, billing_day,
                        category_id, notes, color):
    conn = get_connection()
    conn.execute(
        "UPDATE subscriptions SET name=?,amount=?,billing_day=?,"
        "category_id=?,notes=?,color=? WHERE id=?",
        (name, amount, billing_day, category_id, notes, color, sid))
    conn.commit(); conn.close()


# ── Goals ─────────────────────────────────────────────────────────────────────

def add_goal(name, target, deadline, color, icon):
    conn = get_connection()
    conn.execute(
        "INSERT INTO goals (name,target_amount,deadline,color,icon)"
        " VALUES (?,?,?,?,?)",
        (name, target, deadline, color, icon))
    conn.commit(); conn.close()


def get_goals():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM goals ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def update_goal_amount(gid, amount):
    conn = get_connection()
    conn.execute("UPDATE goals SET current_amount=? WHERE id=?", (amount, gid))
    conn.commit(); conn.close()


def delete_goal(gid):
    conn = get_connection()
    conn.execute("DELETE FROM goals WHERE id=?", (gid,))
    conn.commit(); conn.close()