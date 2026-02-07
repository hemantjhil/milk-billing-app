import sqlite3
from contextlib import contextmanager
from datetime import date


DB_FILE = "milk_billing.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                address TEXT,
                alt_delivery_partner_id INTEGER,
                alt_contact TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (alt_delivery_partner_id) REFERENCES delivery_partners (id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS delivery_partners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                address TEXT,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS managers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS advance_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                customer_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                delivery_partner_id INTEGER NOT NULL,
                manager_id INTEGER NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers (id),
                FOREIGN KEY (item_id) REFERENCES items (id),
                FOREIGN KEY (delivery_partner_id) REFERENCES delivery_partners (id),
                FOREIGN KEY (manager_id) REFERENCES managers (id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS partner_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                delivery_partner_id INTEGER NOT NULL,
                manager_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (delivery_partner_id) REFERENCES delivery_partners (id),
                FOREIGN KEY (manager_id) REFERENCES managers (id),
                FOREIGN KEY (item_id) REFERENCES items (id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        _ensure_column(cur, "customers", "alt_contact", "TEXT")


def _ensure_column(cursor, table_name, column_name, column_type):
    columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing = {col[1] for col in columns}
    if column_name not in existing:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        )


def add_customer(name, contact, address, alt_contact):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO customers (name, contact, address, alt_contact)
            VALUES (?, ?, ?, ?)
            """,
            (name, contact, address, alt_contact or None),
        )


def update_customer(customer_id, name, contact, address, alt_contact):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE customers
            SET name = ?, contact = ?, address = ?, alt_contact = ?
            WHERE id = ?
            """,
            (name, contact, address, alt_contact, customer_id),
        )


def deactivate_customer(customer_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE customers SET active = 0 WHERE id = ?", (customer_id,)
        )


def add_delivery_partner(name, contact, address):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO delivery_partners (name, contact, address)
            VALUES (?, ?, ?)
            """,
            (name, contact, address),
        )


def update_delivery_partner(partner_id, name, contact, address):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE delivery_partners
            SET name = ?, contact = ?, address = ?
            WHERE id = ?
            """,
            (name, contact, address, partner_id),
        )


def deactivate_delivery_partner(partner_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE delivery_partners SET active = 0 WHERE id = ?", (partner_id,)
        )


def add_item(name, price):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO items (name, price) VALUES (?, ?)",
            (name, price),
        )


def update_item(item_id, name, price):
    with get_conn() as conn:
        conn.execute(
            "UPDATE items SET name = ?, price = ? WHERE id = ?",
            (name, price, item_id),
        )


def delete_item(item_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))


def add_manager(name, contact):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO managers (name, contact) VALUES (?, ?)",
            (name, contact),
        )


def update_manager(manager_id, name, contact):
    with get_conn() as conn:
        conn.execute(
            "UPDATE managers SET name = ?, contact = ? WHERE id = ?",
            (name, contact, manager_id),
        )


def delete_manager(manager_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM managers WHERE id = ?", (manager_id,))


def add_advance_payment(customer_id, amount, payment_date, notes):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO advance_payments (customer_id, amount, date, notes)
            VALUES (?, ?, ?, ?)
            """,
            (customer_id, amount, payment_date, notes),
        )


def list_advance_payments(payment_date=None):
    with get_conn() as conn:
        if payment_date:
            return conn.execute(
                """
                SELECT ap.*, c.name AS customer_name
                FROM advance_payments ap
                JOIN customers c ON c.id = ap.customer_id
                WHERE ap.date = ?
                ORDER BY ap.id DESC
                """,
                (payment_date,),
            ).fetchall()
        return conn.execute(
            """
            SELECT ap.*, c.name AS customer_name
            FROM advance_payments ap
            JOIN customers c ON c.id = ap.customer_id
            ORDER BY ap.id DESC
            """
        ).fetchall()


def update_advance_payment(payment_id, customer_id, amount, payment_date, notes):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE advance_payments
            SET customer_id = ?, amount = ?, date = ?, notes = ?
            WHERE id = ?
            """,
            (customer_id, amount, payment_date, notes, payment_id),
        )


def delete_advance_payment(payment_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM advance_payments WHERE id = ?", (payment_id,))


def add_daily_delivery(
    delivery_date,
    customer_id,
    item_id,
    quantity,
    price,
    delivery_partner_id,
    manager_id,
):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO daily_deliveries
            (date, customer_id, item_id, quantity, price, delivery_partner_id, manager_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                delivery_date,
                customer_id,
                item_id,
                quantity,
                price,
                delivery_partner_id,
                manager_id,
            ),
        )


def list_daily_deliveries(delivery_date=None):
    with get_conn() as conn:
        if delivery_date:
            return conn.execute(
                """
                SELECT dd.*, c.name AS customer_name, i.name AS item_name,
                       dp.name AS partner_name, m.name AS manager_name
                FROM daily_deliveries dd
                JOIN customers c ON c.id = dd.customer_id
                JOIN items i ON i.id = dd.item_id
                JOIN delivery_partners dp ON dp.id = dd.delivery_partner_id
                JOIN managers m ON m.id = dd.manager_id
                WHERE dd.date = ?
                ORDER BY dd.id DESC
                """,
                (delivery_date,),
            ).fetchall()
        return conn.execute(
            """
            SELECT dd.*, c.name AS customer_name, i.name AS item_name,
                   dp.name AS partner_name, m.name AS manager_name
            FROM daily_deliveries dd
            JOIN customers c ON c.id = dd.customer_id
            JOIN items i ON i.id = dd.item_id
            JOIN delivery_partners dp ON dp.id = dd.delivery_partner_id
            JOIN managers m ON m.id = dd.manager_id
            ORDER BY dd.id DESC
            """
        ).fetchall()


def update_daily_delivery(
    delivery_id,
    delivery_date,
    customer_id,
    item_id,
    quantity,
    price,
    delivery_partner_id,
    manager_id,
):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE daily_deliveries
            SET date = ?, customer_id = ?, item_id = ?, quantity = ?, price = ?,
                delivery_partner_id = ?, manager_id = ?
            WHERE id = ?
            """,
            (
                delivery_date,
                customer_id,
                item_id,
                quantity,
                price,
                delivery_partner_id,
                manager_id,
                delivery_id,
            ),
        )


def delete_daily_delivery(delivery_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM daily_deliveries WHERE id = ?", (delivery_id,))

def add_partner_allocation(allocation_date, partner_id, manager_id, item_id, quantity):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO partner_allocations
            (date, delivery_partner_id, manager_id, item_id, quantity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (allocation_date, partner_id, manager_id, item_id, quantity),
        )


def list_partner_allocations_all(allocation_date=None):
    with get_conn() as conn:
        if allocation_date:
            return conn.execute(
                """
                SELECT pa.*, i.name AS item_name, m.name AS manager_name,
                       dp.name AS partner_name
                FROM partner_allocations pa
                JOIN items i ON i.id = pa.item_id
                JOIN managers m ON m.id = pa.manager_id
                JOIN delivery_partners dp ON dp.id = pa.delivery_partner_id
                WHERE pa.date = ?
                ORDER BY pa.id DESC
                """,
                (allocation_date,),
            ).fetchall()
        return conn.execute(
            """
            SELECT pa.*, i.name AS item_name, m.name AS manager_name,
                   dp.name AS partner_name
            FROM partner_allocations pa
            JOIN items i ON i.id = pa.item_id
            JOIN managers m ON m.id = pa.manager_id
            JOIN delivery_partners dp ON dp.id = pa.delivery_partner_id
            ORDER BY pa.id DESC
            """
        ).fetchall()


def update_partner_allocation(allocation_id, allocation_date, partner_id, manager_id, item_id, quantity):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE partner_allocations
            SET date = ?, delivery_partner_id = ?, manager_id = ?, item_id = ?, quantity = ?
            WHERE id = ?
            """,
            (allocation_date, partner_id, manager_id, item_id, quantity, allocation_id),
        )


def delete_partner_allocation(allocation_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM partner_allocations WHERE id = ?", (allocation_id,))

def list_customers(active_only=True):
    with get_conn() as conn:
        if active_only:
            return conn.execute(
                "SELECT * FROM customers WHERE active = 1 ORDER BY name"
            ).fetchall()
        return conn.execute("SELECT * FROM customers ORDER BY name").fetchall()


def list_customers_with_balance(search_text=""):
    term = f"%{search_text.strip()}%"
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT c.*,
                   COALESCE((
                       SELECT SUM(dd.quantity * dd.price)
                       FROM daily_deliveries dd
                       WHERE dd.customer_id = c.id
                   ), 0) AS charges,
                   COALESCE((
                       SELECT SUM(ap.amount)
                       FROM advance_payments ap
                       WHERE ap.customer_id = c.id
                   ), 0) AS paid
            FROM customers c
            WHERE c.active = 1
              AND (c.name LIKE ? OR c.contact LIKE ? OR c.address LIKE ?)
            ORDER BY c.name
            """,
            (term, term, term),
        ).fetchall()


def list_delivery_partners(active_only=True):
    with get_conn() as conn:
        if active_only:
            return conn.execute(
                "SELECT * FROM delivery_partners WHERE active = 1 ORDER BY name"
            ).fetchall()
        return conn.execute("SELECT * FROM delivery_partners ORDER BY name").fetchall()


def list_items():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM items ORDER BY name").fetchall()


def list_managers():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM managers ORDER BY name").fetchall()


def list_partner_allocations(partner_id, allocation_date):
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT pa.*, i.name AS item_name, m.name AS manager_name
            FROM partner_allocations pa
            JOIN items i ON i.id = pa.item_id
            JOIN managers m ON m.id = pa.manager_id
            WHERE pa.delivery_partner_id = ? AND pa.date = ?
            ORDER BY pa.id
            """,
            (partner_id, allocation_date),
        ).fetchall()


def list_partner_deliveries(partner_id, delivery_date):
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT dd.*, c.name AS customer_name, i.name AS item_name, m.name AS manager_name
            FROM daily_deliveries dd
            JOIN customers c ON c.id = dd.customer_id
            JOIN items i ON i.id = dd.item_id
            JOIN managers m ON m.id = dd.manager_id
            WHERE dd.delivery_partner_id = ? AND dd.date = ?
            ORDER BY dd.id
            """,
            (partner_id, delivery_date),
        ).fetchall()


def partner_remaining(partner_id, day):
    with get_conn() as conn:
        alloc = conn.execute(
            """
            SELECT COALESCE(SUM(quantity), 0) AS qty
            FROM partner_allocations
            WHERE delivery_partner_id = ? AND date = ?
            """,
            (partner_id, day),
        ).fetchone()["qty"]
        delivered = conn.execute(
            """
            SELECT COALESCE(SUM(quantity), 0) AS qty
            FROM daily_deliveries
            WHERE delivery_partner_id = ? AND date = ?
            """,
            (partner_id, day),
        ).fetchone()["qty"]
        return alloc - delivered


def monthly_customer_statement(customer_id, month_yyyy_mm):
    with get_conn() as conn:
        deliveries = conn.execute(
            """
            SELECT dd.date, dd.quantity, dd.price,
                   i.name AS item_name,
                   dp.name AS partner_name
            FROM daily_deliveries dd
            JOIN items i ON i.id = dd.item_id
            JOIN delivery_partners dp ON dp.id = dd.delivery_partner_id
            WHERE dd.customer_id = ?
              AND substr(dd.date, 1, 7) = ?
            ORDER BY dd.date
            """,
            (customer_id, month_yyyy_mm),
        ).fetchall()
        payments = conn.execute(
            """
            SELECT date, amount, notes
            FROM advance_payments
            WHERE customer_id = ?
              AND substr(date, 1, 7) = ?
            ORDER BY date
            """,
            (customer_id, month_yyyy_mm),
        ).fetchall()
        return deliveries, payments


def customer_statement_range(customer_id, start_date, end_date):
    with get_conn() as conn:
        deliveries = conn.execute(
            """
            SELECT dd.date, dd.quantity, dd.price,
                   i.name AS item_name,
                   dp.name AS partner_name
            FROM daily_deliveries dd
            JOIN items i ON i.id = dd.item_id
            JOIN delivery_partners dp ON dp.id = dd.delivery_partner_id
            WHERE dd.customer_id = ?
              AND dd.date BETWEEN ? AND ?
            ORDER BY dd.date
            """,
            (customer_id, start_date, end_date),
        ).fetchall()
        payments = conn.execute(
            """
            SELECT date, amount, notes
            FROM advance_payments
            WHERE customer_id = ?
              AND date BETWEEN ? AND ?
            ORDER BY date
            """,
            (customer_id, start_date, end_date),
        ).fetchall()
        return deliveries, payments


def customer_summary_range(customer_id, start_date, end_date):
    with get_conn() as conn:
        totals = conn.execute(
            """
            SELECT
                COALESCE(SUM(dd.quantity), 0) AS total_qty,
                COALESCE(SUM(dd.quantity * dd.price), 0) AS total_amount
            FROM daily_deliveries dd
            WHERE dd.customer_id = ?
              AND dd.date BETWEEN ? AND ?
            """,
            (customer_id, start_date, end_date),
        ).fetchone()
        paid = conn.execute(
            """
            SELECT COALESCE(SUM(ap.amount), 0) AS total_paid
            FROM advance_payments ap
            WHERE ap.customer_id = ?
              AND ap.date BETWEEN ? AND ?
            """,
            (customer_id, start_date, end_date),
        ).fetchone()
        return totals["total_qty"], totals["total_amount"], paid["total_paid"]


def get_customer(customer_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()


def get_setting(key, default=None):
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key, value):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )


def today_str():
    return date.today().strftime("%Y-%m-%d")
