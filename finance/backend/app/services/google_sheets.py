import asyncio
import time

from app.config import settings


class GoogleSheetsService:
    """Сервис для получения данных из Google Sheets с кешированием."""

    def __init__(self):
        self._cache: list[list[str]] | None = None
        self._cache_time: float = 0
        self._cache_ttl: int = 300  # 5 минут
        self._service = None

    def _get_service(self):
        if self._service is not None:
            return self._service

        if not settings.google_service_account_key or not settings.google_sheet_id:
            return None

        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_file(
            settings.google_service_account_key, scopes=scopes
        )
        self._service = build("sheets", "v4", credentials=creds)
        return self._service

    def _fetch_data(self, range_name: str | None = None) -> list[list[str]]:
        """Синхронный вызов Google Sheets API (запускается в отдельном потоке)."""
        service = self._get_service()
        if service is None:
            return []

        sheet_range = range_name or settings.google_sheet_range
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=settings.google_sheet_id, range=sheet_range)
            .execute()
        )
        return result.get("values", [])

    async def get_data(self, range_name: str | None = None) -> list[list[str]]:
        """Получить данные из таблицы (с кешем 5 мин)."""
        now = time.time()
        if self._cache and (now - self._cache_time) < self._cache_ttl:
            return self._cache

        rows = await asyncio.to_thread(self._fetch_data, range_name)
        self._cache = rows
        self._cache_time = time.time()
        return rows


sheets_service = GoogleSheetsService()
