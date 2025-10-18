#!/usr/bin/env python3
"""Simple migration: add asin to products and source to price_history if missing.

This script is safe to run multiple times.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'pricepulse.db')

def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table});")
    cols = [r[1] for r in cur.fetchall()]
    return column in cols

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Nothing to do.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        if not column_exists(cur, 'products', 'asin'):
            print('Adding asin column to products...')
            cur.execute("ALTER TABLE products ADD COLUMN asin TEXT;")
        else:
            print('Column products.asin already exists')

        if not column_exists(cur, 'products', 'source'):
            print('Adding source column to products...')
            cur.execute("ALTER TABLE products ADD COLUMN source TEXT;")
        else:
            print('Column products.source already exists')

        if not column_exists(cur, 'price_history', 'source'):
            print('Adding source column to price_history...')
            cur.execute("ALTER TABLE price_history ADD COLUMN source TEXT;")
        else:
            print('Column price_history.source already exists')

        conn.commit()
        print('Migration completed.')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
