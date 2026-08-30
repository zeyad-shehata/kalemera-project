from datetime import datetime, timedelta, time, timezone
from typing import Dict, Any, List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.report_repository import report_repository

class ReportService:
    async def get_dashboard_summary(self, db: AsyncSession) -> Dict[str, Any]:
        return await report_repository.get_dashboard_summary(db)

    async def get_sales_report(
        self, db: AsyncSession, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = (
                datetime.strptime(end_date, "%Y-%m-%d")
                + timedelta(days=1)
                - timedelta(seconds=1)
            )
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD."
            )

        return await report_repository.get_sales_by_date(db, start_dt, end_dt)

    async def get_accounting_report(
        self, db: AsyncSession, period: str = "today"
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        if period == "today":
            start_time = datetime.combine(now.date(), time.min)
        elif period == "week":
            start_time = datetime.combine((now - timedelta(days=7)).date(), time.min)
        else:  # month
            start_time = datetime.combine((now - timedelta(days=30)).date(), time.min)

        return await report_repository.get_accounting_data(db, start_time)

report_service = ReportService()
