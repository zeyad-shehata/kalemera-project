from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.security import admin_required
from app.services.report_service import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/dashboard")
async def get_dashboard_summary(
    admin_user=Depends(admin_required), db: AsyncSession = Depends(get_db)
):
    return await report_service.get_dashboard_summary(db)

@router.get("/sales")
async def get_sales_report(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    return await report_service.get_sales_report(db, start_date, end_date)

@router.get("/accounting")
async def get_accounting_report(
    period: str = Query("today", description="today, week, or month"),
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    return await report_service.get_accounting_report(db, period)
