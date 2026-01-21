#!/usr/bin/env python3
"""
Rebuild parts.db from parts.csv

Run from any directory:
    python3 rebuild_db.py

Or make executable and run directly:
    chmod +x rebuild_db.py
    ./rebuild_db.py
"""

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

# Script directory (where parts.csv and parts.db live)
SCRIPT_DIR = Path(__file__).parent.resolve()
CSV_PATH = SCRIPT_DIR / "parts.csv"
DB_PATH = SCRIPT_DIR / "parts.db"


def main():
    print("=" * 50)
    print("Rebuild parts.db from parts.csv")
    print("=" * 50)
    
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found")
        return 1
    
    # Backup existing database
    if DB_PATH.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = DB_PATH.parent / f"parts.db.{timestamp}.bak"
        DB_PATH.rename(backup)
        print(f"Backup: {backup}")
    
    # Read CSV
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    print(f"Read {len(rows)} parts from {CSV_PATH.name}")
    
    # Create database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table
    columns_def = ", ".join(f'"{col}" TEXT' for col in fieldnames)
    cursor.execute(f"CREATE TABLE parts ({columns_def});")
    
    # Insert rows
    placeholders = ", ".join("?" for _ in fieldnames)
    columns_list = ", ".join(f'"{col}"' for col in fieldnames)
    insert_sql = f"INSERT INTO parts ({columns_list}) VALUES ({placeholders});"
    
    for row in rows:
        values = [row.get(col, "") for col in fieldnames]
        cursor.execute(insert_sql, values)
    
    conn.commit()
    conn.close()
    
    print(f"Created {DB_PATH.name} with {len(rows)} parts")
    print("=" * 50)
    print("DONE")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    exit(main())
