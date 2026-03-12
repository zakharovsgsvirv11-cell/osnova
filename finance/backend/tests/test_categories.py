"""Тесты CRUD категорий."""

import pytest


@pytest.mark.asyncio
async def test_create_category(client):
    response = await client.post("/api/v1/categories", json={
        "name": "Ипотека",
        "type": "расход",
        "color": "#F44336",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ипотека"
    assert data["type"] == "расход"
    assert data["color"] == "#F44336"
    assert data["is_active"] == 1


@pytest.mark.asyncio
async def test_create_category_income(client):
    response = await client.post("/api/v1/categories", json={
        "name": "Зарплата",
        "type": "доход",
    })
    assert response.status_code == 201
    assert response.json()["type"] == "доход"


@pytest.mark.asyncio
async def test_create_category_invalid_type(client):
    response = await client.post("/api/v1/categories", json={
        "name": "Тест",
        "type": "income",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_categories(client):
    await client.post("/api/v1/categories", json={"name": "Еда", "type": "расход"})
    await client.post("/api/v1/categories", json={"name": "Зарплата", "type": "доход"})

    response = await client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_categories_by_type(client):
    await client.post("/api/v1/categories", json={"name": "Еда", "type": "расход"})
    await client.post("/api/v1/categories", json={"name": "Зарплата", "type": "доход"})

    response = await client.get("/api/v1/categories", params={"type": "расход"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "расход"


@pytest.mark.asyncio
async def test_update_category(client):
    create = await client.post("/api/v1/categories", json={"name": "Еда", "type": "расход"})
    cat_id = create.json()["id"]

    response = await client.put(f"/api/v1/categories/{cat_id}", json={"name": "Продукты"})
    assert response.status_code == 200
    assert response.json()["name"] == "Продукты"


@pytest.mark.asyncio
async def test_update_nonexistent_category(client):
    response = await client.put("/api/v1/categories/999", json={"name": "X"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Категория не найдена"


@pytest.mark.asyncio
async def test_delete_category(client):
    create = await client.post("/api/v1/categories", json={"name": "Удалить", "type": "расход"})
    cat_id = create.json()["id"]

    response = await client.delete(f"/api/v1/categories/{cat_id}")
    assert response.status_code == 204

    listing = await client.get("/api/v1/categories")
    assert len(listing.json()) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_category(client):
    response = await client.delete("/api/v1/categories/999")
    assert response.status_code == 404
