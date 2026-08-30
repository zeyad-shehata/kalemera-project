import os
import shutil
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any
from pathlib import Path

from app.config import settings, BACKEND_DIR

class BackupService:
    def __init__(self):
        self.backup_dir = Path(settings.BACKUPS_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        # Parse database path from settings.DATABASE_URL
        # e.g. "sqlite+aiosqlite:///./kalemera.db" -> BACKEND_DIR / "kalemera.db"
        db_url = settings.DATABASE_URL
        if "sqlite" in db_url:
            clean_path = db_url.split(":///")[-1]
            if clean_path.startswith("./"):
                self.db_path = BACKEND_DIR / clean_path[2:]
            else:
                self.db_path = Path(clean_path)
        else:
            self.db_path = BACKEND_DIR / "kalemera.db"

    def create_backup(self) -> Dict[str, Any]:
        """Creates an atomic SQLite backup and enforces retention policy."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found at {self.db_path}")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"kalemera_backup_{timestamp}.db"
        backup_filepath = self.backup_dir / backup_filename

        # Use SQLite online backup API for transactionally safe backup
        src_conn = sqlite3.connect(str(self.db_path))
        dest_conn = sqlite3.connect(str(backup_filepath))
        try:
            with dest_conn:
                src_conn.backup(dest_conn)
        finally:
            dest_conn.close()
            src_conn.close()

        file_size = backup_filepath.stat().st_size

        # Enforce rolling retention policy (keep latest N backups)
        self._enforce_retention()

        return {
            "filename": backup_filename,
            "path": str(backup_filepath),
            "size_bytes": file_size,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_backups": len(self.list_backups())
        }

    def list_backups(self) -> List[Dict[str, Any]]:
        """Lists all existing backups sorted newest to oldest."""
        backups = []
        if not self.backup_dir.exists():
            return backups

        for f in self.backup_dir.glob("kalemera_backup_*.db"):
            stat = f.stat()
            backups.append({
                "filename": f.name,
                "path": str(f),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            })

        # Sort newest first
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    def _enforce_retention(self) -> None:
        """Purges old backups exceeding settings.BACKUP_RETENTION_COUNT."""
        backups = self.list_backups()
        max_allowed = settings.BACKUP_RETENTION_COUNT
        if len(backups) > max_allowed:
            for old_backup in backups[max_allowed:]:
                try:
                    os.remove(old_backup["path"])
                except Exception:
                    pass

    def restore_backup(self, backup_filename: str) -> bool:
        """Restores the database from a specified backup file."""
        backup_filepath = self.backup_dir / backup_filename
        if not backup_filepath.exists():
            raise FileNotFoundError(f"Backup {backup_filename} not found.")

        # Atomic copy back to primary DB location
        shutil.copy2(str(backup_filepath), str(self.db_path))
        return True


backup_service = BackupService()
