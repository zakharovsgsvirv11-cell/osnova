"""Тесты отчётов и статистики — ключевой блок, где была найдена проблема."""

import pytest

from app.models.category import Category
from app.models.transaction import Transaction


@pytest.fixture
async def populated_db(db, test_user):
    """Создать тестовые категории и транзакции."""
    cat_expense = Category(user_id=test_user.id, name="Ипотека", type="расход", color="#F44336")
    cat_income = Category(user_id=test_user.id, name="Зарплата", type="доход", color="#4CAF50")
    db.add_all([cat_expense, cat_income])
    await db.commit()
    await db.refresh(cat_expense)
    await db.refresh(cat_income)

    transactions = [
        Transaction(user_id=test_user.id, category_id=cat_expense.id, amount=88000, type="расход", date="2026-03-12", description="Ипотека"),
        Transaction(user_id=test_user.id, category_id=cat_expense.id, amount=15000, type="расход", date="2026-03-15", description="Коммуналка"),
        Transaction(user_id=test_user.id, category_id=cat_income.id, amount=200000, type="доход", date="2026-03-01", description="Зарплата"),
        Transaction(user_id=test_user.id, category_id=cat_income.id, amount=50000, type="доход", date="2026-02-01", description="Зарплата февраль"),
        Transaction(user_id=test_user.id, category_id=cat_expense.id, amount=30000, type="расход", date="2026-02-10", description="Ипотека февраль"),
    ]
    db.add_all(transactions)
    await db.commit()

    return {"expense_cat": cat_expense, "income_cat": cat_income}


@pytest.mark.asyncio
async def test_balance(client, populated_db):
    response = await client.get("/api/v1/reports/balance")
    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 250000.0
    assert data["total_expense"] == 133000.0
    assert data["balance"] == 117000.0


@pytest.mark.asyncio
async def test_monthly_summary(client, populated_db):
    response = await client.get("/api/v1/reports/monthly-summary", params={"year": 2026})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # февраль и март

    months = {item["month"]: item for item in data}

    assert "2026-03" in months
    march = months["2026-03"]
    assert march["income"] == 200000.0
    assert march["expense"] == 103000.0
    assert march["balance"] == 97000.0

    assert "2026-02" in months
    feb = months["2026-02"]
    assert feb["income"] == 50000.0
    assert feb["expense"] == 30000.0
    assert feb["balance"] == 20000.0


@pytest.mark.asyncio
async def test_monthly_summary_empty_year(client, populated_db):
    response = await client.get("/api/v1/reports/monthly-summary", params={"year": 2025})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_category_breakdown(client, populated_db):
    response = await client.get("/api/v1/reports/category-breakdown", params={
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "type": "расход",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category_name"] == "Ипотека"
    assert data[0]["total"] == 133000.0
    assert data[0]["percentage"] == 100.0


@pytest.mark.asyncio
async def test_category_breakdown_invalid_type(client):
    response = await client.get("/api/v1/reports/category-breakdown", params={
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "type": "expense",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_trend(client, populated_db):
    response = await client.get("/api/v1/reports/trend", params={"months": 12})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    months = {item["month"]: item for item in data}
    assert months["2026-03"]["income"] == 200000.0
    assert months["2026-03"]["expense"] == 103000.0


@pytest.mark.asyncio
async def test_balance_empty(client):
    response = await client.get("/api/v1/reports/balance")
    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 0.0
    assert data["total_expense"] == 0.0
    assert data["balance"] == 0.0
