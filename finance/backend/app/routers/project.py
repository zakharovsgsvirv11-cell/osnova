from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.services.google_sheets import sheets_service

router = APIRouter(prefix="/project", tags=["project"])


@router.get("/data")
async def project_data(user: User = Depends(get_current_user)):
    """Сырые данные из Google Sheets."""
    rows = sheets_service.get_data()
    if not rows:
        return {"headers": [], "rows": []}
    return {"headers": rows[0], "rows": rows[1:]}


@router.get("/summary")
async def project_summary(user: User = Depends(get_current_user)):
    """Агрегированная сводка по проекту (будет расширена позже)."""
    rows = sheets_service.get_data()
    return {
        "total_rows": len(rows) - 1 if rows else 0,
        "headers": rows[0] if rows else [],
        "message": "Детальная аналитика проекта будет добавлена позже",
    }
