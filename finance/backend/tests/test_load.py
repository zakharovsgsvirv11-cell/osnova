"""Нагрузочные тесты API — проверяем производительность под нагрузкой."""

import asyncio
import time

import pytest

from app.models.category import Category
from app.models.transaction import Transaction


@pytest.fixture
async def heavy_db(db, test_user):
    """Создать 1000 транзакций для нагрузочного тестирования."""
    cat = Category(user_id=test_user.id, name="Тест", type="расход", color="#F44336")
    db.add(cat)
    await db.commit()
    await db.refresh(cat)

    transactions = [
        Transaction(
            user_id=test_user.id,
            category_id=cat.id,
            amount=100.0 + i,
            type="расход" if i % 2 == 0 else "доход",
            date=f"2026-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
            description=f"Транзакция #{i}",
        )
        for i in range(1000)
    ]
    db.add_all(transactions)
    await db.commit()
    return cat


@pytest.mark.asyncio
async def test_load_list_transactions(client, heavy_db):
    """1000 транзакций — пагинация должна работать быстро."""
    start = time.perf_counter()
    tasks = [client.get("/api/v1/transactions", params={"page": i, "per_page": 20}) for i in range(1, 11)]
    responses = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    for r in responses:
        assert r.status_code == 200

    assert responses[0].json()["total"] == 1000
    assert elapsed < 5.0, f"10 параллельных запросов списка заняли {elapsed:.2f}с (лимит 5с)"


@pytest.mark.asyncio
async def test_load_balance(client, heavy_db):
    """Баланс по 1000 транзакциям."""
    start = time.perf_counter()
    tasks = [client.get("/api/v1/reports/balance") for _ in range(20)]
    responses = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    for r in responses:
        assert r.status_code == 200
        data = r.json()
        assert data["total_income"] > 0
        assert data["total_expense"] > 0

    assert elapsed < 5.0, f"20 параллельных запросов баланса заняли {elapsed:.2f}с (лимит 5с)"


@pytest.mark.asyncio
async def test_load_monthly_summary(client, heavy_db):
    """Месячная сводка по 1000 транзакциям."""
    start = time.perf_counter()
    tasks = [client.get("/api/v1/reports/monthly-summary", params={"year": 2026}) for _ in range(20)]
    responses = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    for r in responses:
        assert r.status_code == 200
        assert len(r.json()) > 0

    assert elapsed < 5.0, f"20 параллельных запросов сводки заняли {elapsed:.2f}с (лимит 5с)"


@pytest.mark.asyncio
async def test_load_trend(client, heavy_db):
    """Тренд по 1000 транзакциям."""
    start = time.perf_counter()
    tasks = [client.get("/api/v1/reports/trend", params={"months": 12}) for _ in range(20)]
    responses = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    for r in responses:
        assert r.status_code == 200

    assert elapsed < 5.0, f"20 параллельных запросов тренда заняли {elapsed:.2f}с (лимит 5с)"


@pytest.mark.asyncio
async def test_load_create_transactions(client, heavy_db):
    """Массовое создание транзакций."""
    start = time.perf_counter()
    tasks = [
        client.post("/api/v1/transactions", json={
            "category_id": heavy_db.id,
            "amount": 500.0 + i,
            "type": "расход",
            "date": f"2026-03-{(i % 28) + 1:02d}",
            "description": f"Нагрузка #{i}",
        })
        for i in range(50)
    ]
    responses = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    for r in responses:
        assert r.status_code == 201

    assert elapsed < 10.0, f"50 параллельных POST заняли {elapsed:.2f}с (лимит 10с)"


@pytest.mark.asyncio
async def test_load_category_breakdown(client, heavy_db):
    """Разбивка по категориям при 1000 транзакциях."""
    start = time.perf_counter()
    tasks = [
        client.get("/api/v1/reports/category-breakdown", params={
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "type": "расход",
        })
        for _ in range(20)
    ]
    responses = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    for r in responses:
        assert r.status_code == 200

    assert elapsed < 5.0, f"20 параллельных запросов breakdown заняли {elapsed:.2f}с (лимит 5с)"
