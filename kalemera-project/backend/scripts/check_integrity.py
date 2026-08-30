#!/usr/bin/env python3
"""CLI utility for Kalmera Database Health & Integrity Verification."""
import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings, BACKEND_DIR

def check_integrity():
    db_path = BACKEND_DIR / "kalemera.db"
    print(f"=== Checking SQLite Database Integrity at {db_path} ===")
    
    if not db_path.exists():
        print("❌ Database file does not exist!")
        sys.exit(1)
        
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 1. PRAGMA integrity_check
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchall()
    print(f"1. Integrity Check: {integrity}")
    
    # 2. PRAGMA foreign_key_check
    cursor.execute("PRAGMA foreign_key_check;")
    fk_errors = cursor.fetchall()
    if fk_errors:
        print(f"[WARNING] Foreign Key Violations Found: {fk_errors}")
    else:
        print("2. Foreign Key Check: [OK] 0 violations found.")
        
    # 3. Table summary
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"3. Registered Tables ({len(tables)}):")
    for t in tables:
        cursor.execute(f"SELECT count(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        print(f"   - {t}: {cnt} rows")
        
    conn.close()
    print("=== Database Health Check Completed ===")

if __name__ == "__main__":
    check_integrity()
