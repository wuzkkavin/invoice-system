import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "invoices.db")
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT NOT NULL,
            date TEXT NOT NULL,
            seller TEXT,
            seller_tax_id TEXT,
            product TEXT,
            amount REAL,
            tax REAL,
            image_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def insert_invoice(data, image_filename=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO invoices (invoice_no, date, seller, seller_tax_id, product, amount, tax, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("invoice_no"),
        data.get("date"),
        data.get("seller"),
        data.get("seller_tax_id"),
        data.get("product"),
        data.get("amount"),
        data.get("tax"),
        image_filename
    ))
    conn.commit()
    invoice_id = cursor.lastrowid
    conn.close()
    return invoice_id


def update_invoice(invoice_id, data, image_filename=None):
    conn = get_connection()
    cursor = conn.cursor()
    if image_filename:
        cursor.execute("""
            UPDATE invoices SET
                invoice_no=?, date=?, seller=?, seller_tax_id=?,
                product=?, amount=?, tax=?, image_path=?
            WHERE id=?
        """, (
            data.get("invoice_no"),
            data.get("date"),
            data.get("seller"),
            data.get("seller_tax_id"),
            data.get("product"),
            data.get("amount"),
            data.get("tax"),
            image_filename,
            invoice_id
        ))
    else:
        cursor.execute("""
            UPDATE invoices SET
                invoice_no=?, date=?, seller=?, seller_tax_id=?,
                product=?, amount=?, tax=?
            WHERE id=?
        """, (
            data.get("invoice_no"),
            data.get("date"),
            data.get("seller"),
            data.get("seller_tax_id"),
            data.get("product"),
            data.get("amount"),
            data.get("tax"),
            invoice_id
        ))
    conn.commit()
    conn.close()


def delete_invoice(invoice_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT image_path FROM invoices WHERE id=?", (invoice_id,))
    row = cursor.fetchone()
    if row and row["image_path"]:
        img_path = os.path.join(IMAGES_DIR, row["image_path"])
        if os.path.exists(img_path):
            os.remove(img_path)
    cursor.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
    conn.commit()
    conn.close()


def search_invoices(invoice_no="", seller="", product="", amount_min=None, amount_max=None,
                    date_start="", date_end="", seller_tax_id=""):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM invoices WHERE 1=1"
    params = []

    if invoice_no:
        query += " AND invoice_no LIKE ?"
        params.append(f"%{invoice_no}%")
    if seller:
        query += " AND seller LIKE ?"
        params.append(f"%{seller}%")
    if product:
        query += " AND product LIKE ?"
        params.append(f"%{product}%")
    if seller_tax_id:
        query += " AND seller_tax_id LIKE ?"
        params.append(f"%{seller_tax_id}%")
    if amount_min is not None:
        query += " AND amount >= ?"
        params.append(amount_min)
    if amount_max is not None:
        query += " AND amount <= ?"
        params.append(amount_max)
    if date_start:
        query += " AND date >= ?"
        params.append(date_start)
    if date_end:
        query += " AND date <= ?"
        params.append(date_end)

    query += " ORDER BY date DESC, id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_invoices():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices ORDER BY date DESC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_invoice_by_id(invoice_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


init_db()