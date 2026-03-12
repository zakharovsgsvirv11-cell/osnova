"""Тесты CRUD транзакций."""

import pytest

from app.models.category import Category


@pytest.fixture
async def expense_category(db, test_user):
    cat = Category(user_id=test_user.id, name="Ипотека", type="расход", color="#F44336")
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@pytest.fixture
async def income_category(db, test_user):
    cat = Category(user_id=test_user.id, name="Зарплата", type="доход", color="#4CAF50")
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@pytest.mark.asyncio
async def test_create_transaction(client, expense_category):
    response = await client.post("/api/v1/transactions", json={
        "category_id": expense_category.id,
        "amount": 88000,
        "type": "расход",
        "description": "Ипотека за март",
        "date": "2026-03-12",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 88000
    assert data["type"] == "расход"
    assert data["description"] == "Ипотека за март"
    assert data["date"] == "2026-03-12"


@pytest.mark.asyncio
async def test_create_transaction_invalid_type(client, expense_category):
    response = await client.post("/api/v1/transactions", json={
        "category_id": expense_category.id,
        "amount": 100,
        "type": "expense",
        "date": "2026-03-12",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_transaction_negative_amount(client, expense_category):
    response = await client.post("/api/v1/transactions", json={
        "category_id": expense_category.id,
        "amount": -100,
        "type": "расход",
        "date": "2026-03-12",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_transaction_invalid_date(client, expense_category):
    response = await client.post("/api/v1/transactions", json={
        "category_id": expense_category.id,
        "amount": 100,
        "type": "расход",
        "date": "12.03.2026",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_transactions(client, expense_category):
    await client.post("/api/v1/transactions", json={
        "category_id": expense_category.id,
        "amount": 1000,
        "type": "расход",
        "date": "2026-03-01",
    })
    await client.post("/api/v1/transactions", json={
        "category_id": expense_category.id,
        "amount": 2000,
        "type": "расход",
        "date": "2026-03-02",
    })

    response = await client.get("/api/v1/transactions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_transactions_filter_by_type(client, expense_category, income_category):
    await client.post("/api/v1/transactions", json={
        "category_id": expense_category.id,
        "amount": 1000,
        "type": "расход",
        "date": "2026-03-01",
    })
    await client.post("/api/v1/transactions", json={
        "category_id": income_category.id,
        "amount": 5000,
        "type": "доход",
        "date": "2026-03-01",
    })

    response = await client.get("/api/v1/transactions", params={"type": "доход"})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["type"] == "доход"


@pytest.mark.asyncio
async def test_list_transactions_pagination(client, expense_category):
    for i in range(5):
        await client.post("/api/v1/transactions", json={
            "category_id": expense_category.id,
            "amount": 100 * (i + 1),
            "type": "расход",
            "date": f"2026-03-{i + 1:02d}",
        })

    response = await client.get("/api/v1/transactions", params={"per_page": 2, "page": 1})
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["per_page"] == 2


@pytest.mark.asyncio
async def test_update_transaction(client, expense_category):
    create = await client.post("/api/v1/transactions", json={
        "category_id": expense_category.id,
        "amount": 1000,
        "type": "расход",
        "date": "2026-03-01",
    })
    tx_id = create.json()["id"]

    response = await client.put(f"/api/v1/transactions/{tx_id}", json={
        "amount": 2000,
        "description": "Обновлено",
    })
    assert response.status_code == 200
    assert response.json()["amount"] == 2000
    assert response.json()["description"] == "Обновлено"


@pytest.mark.asyncio
async def test_update_nonexistent_transaction(client):
    response = await client.put("/api/v1/transactions/999", json={"amount": 100})
    assert response.status_code == 404
    assert response.json()["detail"] == "Транзакция не найдена"


@pytest.mark.asyncio
async def test_delete_transaction(client, expense_category):
    create = await client.post("/api/v1/transactions", json={
        "category_id": expense_category.id,
        "amount": 1000,
        "type": "расход",
        "date": "2026-03-01",
    })
    tx_id = create.json()["id"]

    response = await client.delete(f"/api/v1/transactions/{tx_id}")
    assert response.status_code == 204

    listing = await client.get("/api/v1/transactions")
    assert listing.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_transaction(client):
    response = await client.delete("/api/v1/transactions/999")
    assert response.status_code == 404
