import sqlite3
import os
import uuid
from calendar import monthrange
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_HERE, "financeapp_pro.db")


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
        ("Alimentacao",  "#FF6B6B", "AL", "expense"),
        ("Transporte",   "#4ECDC4", "TR", "expense"),
        ("Moradia",      "#45B7D1", "MO", "expense"),
        ("Saude",        "#96CEB4", "SA", "expense"),
        ("Lazer",        "#F7B731", "LZ", "expense"),
        ("Educacao",     "#A29BFE", "ED", "expense"),
        ("Vestuario",    "#FD79A8", "VS", "expense"),
        ("Streaming",    "#6C63FF", "ST", "expense"),
        ("Mercado",      "#00B894", "ME", "expense"),
        ("Outros",       "#B2BEC3", "OT", "expense"),
        ("Salario",      "#00B894", "SL", "income"),
        ("Freelance",    "#00CEC9", "FL", "income"),
        ("Investimentos","#FDCB6E", "IV", "income"),
        ("Outros Ganhos","#74B9FF", "OG", "income"),
    ]
    for row in defaults:
        c.execute(
            "INSERT OR IGNORE INTO categories (name,color,icon,type) VALUES (?,?,?,?)",
            row)
    # Migração: adiciona colunas de parcelamento se não existirem
    existing = {r[1] for r in c.execute("PRAGMA table_info(transactions)").fetchall()}
    for col, definition in [
        ("installment_total",   "INTEGER DEFAULT 0"),
        ("installment_current", "INTEGER DEFAULT 0"),
        ("installment_group",   "TEXT DEFAULT NULL"),
    ]:
        if col not in existing:
            c.execute(f"ALTER TABLE transactions ADD COLUMN {col} {definition}")

    conn.commit()
    conn.close()


def _add_months(date_str: str, n: int) -> str:
    """Retorna date_str + n meses, respeitando fim de mês."""
    d     = datetime.strptime(date_str, "%Y-%m-%d")
    month = d.month - 1 + n
    year  = d.year + month // 12
    month = month % 12 + 1
    day   = min(d.day, monthrange(year, month)[1])
    return f"{year}-{month:02d}-{day:02d}"


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


# ── Installments ──────────────────────────────────────────────────────────────

def add_installment_transactions(description, total_amount, category_id,
                                  start_date, notes, num_installments):
    """Cria N transações de despesa distribuídas mês a mês."""
    group_id  = uuid.uuid4().hex[:12]
    inst_amt  = round(total_amount / num_installments, 2)
    first_amt = round(total_amount - inst_amt * (num_installments - 1), 2)
    conn = get_connection()
    for i in range(num_installments):
        date   = _add_months(start_date, i)
        amount = first_amt if i == 0 else inst_amt
        conn.execute(
            "INSERT INTO transactions "
            "(description,amount,type,category_id,date,notes,"
            " installment_total,installment_current,installment_group)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (description, amount, "expense", category_id, date, notes,
             num_installments, i + 1, group_id))
    conn.commit(); conn.close()


def get_invoice_transactions(month, year):
    """Todas as despesas de um mês/ano para simulação de fatura."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT t.*,
               c.name  AS category_name,
               c.color AS category_color
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE strftime('%m', t.date) = ?
          AND strftime('%Y', t.date) = ?
          AND t.type = 'expense'
        ORDER BY t.date DESC, t.created_at DESC
    """, (f"{month:02d}", str(year))).fetchall()
    conn.close()
    return rows


def get_installment_projection(from_year, from_month, num_months=6):
    """Total de parcelamentos comprometidos para os próximos N meses."""
    from_date = f"{from_year}-{from_month:02d}-01"
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            CAST(strftime('%Y', date) AS INTEGER) AS yr,
            CAST(strftime('%m', date) AS INTEGER) AS mo,
            SUM(amount) AS total
        FROM transactions
        WHERE installment_total > 0
          AND type = 'expense'
          AND date >= ?
        GROUP BY yr, mo
        ORDER BY yr, mo
    """, (from_date,)).fetchall()
    conn.close()

    result = []
    for i in range(num_months):
        m     = (from_month - 1 + i) % 12 + 1
        y     = from_year + (from_month - 1 + i) // 12
        total = next(
            (float(r["total"]) for r in rows if r["yr"] == y and r["mo"] == m),
            0.0)
        result.append((y, m, total))
    return result


def get_active_installment_groups():
    """Grupos de parcelamento com parcelas futuras pendentes."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            t.installment_group,
            t.description,
            MAX(t.installment_total)  AS installment_total,
            SUM(CASE WHEN t.date < date('now','start of month')
                     THEN 1 ELSE 0 END) AS paid_count,
            SUM(CASE WHEN t.date >= date('now','start of month')
                     THEN 1 ELSE 0 END) AS remaining_count,
            SUM(CASE WHEN t.date >= date('now','start of month')
                     THEN t.amount ELSE 0 END) AS remaining_total,
            AVG(t.amount)  AS monthly_amount,
            MAX(t.date)    AS end_date,
            MIN(CASE WHEN t.date >= date('now','start of month')
                     THEN t.date ELSE NULL END) AS next_date,
            c.name  AS category_name,
            c.color AS category_color
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.installment_total > 0
          AND t.installment_group IS NOT NULL
          AND t.type = 'expense'
        GROUP BY t.installment_group
        HAVING remaining_count > 0
        ORDER BY next_date
    """).fetchall()
    conn.close()
    return rows