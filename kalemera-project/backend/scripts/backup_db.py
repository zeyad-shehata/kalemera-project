#!/usr/bin/env python3
"""CLI utility for Kalmera Database Backup and Retention Management."""
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.backup_service import backup_service

def main():
    print("=== KALMERA Database Backup Utility ===")
    try:
        result = backup_service.create_backup()
        print(f"[OK] Backup created successfully: {result['filename']}")
        print(f"Location: {result['path']}")
        print(f"Size: {result['size_bytes'] / 1024:.1f} KB")
        print(f"Total stored backups: {result['total_backups']}")
    except Exception as e:
        print(f"[ERROR] Backup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
