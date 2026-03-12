"""Тесты блока авторизации."""

import pytest


@pytest.mark.asyncio
async def test_login_success(client, test_user):
    response = await client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "testpass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client, test_user):
    response = await client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "wrongpassword",
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Неверные учётные данные"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post("/api/v1/auth/login", json={
        "username": "nobody",
        "password": "pass",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me(client, test_user):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["id"] == test_user.id


@pytest.mark.asyncio
async def test_me_unauthorized(client):
    client.headers.pop("Authorization", None)
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_logout(client):
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["detail"] == "Выход выполнен"
