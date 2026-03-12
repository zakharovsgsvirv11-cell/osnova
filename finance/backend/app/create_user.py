"""CLI-скрипт для создания пользователя.

Использование:
    python -m app.create_user --username admin --password yourpassword
"""

import argparse
import asyncio

from sqlalchemy import select

from app.database import async_session, engine
from app.models.user import Base, User
from app.services.auth import hash_password


async def create_user(username: str, password: str):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            print(f"Пользователь '{username}' уже существует.")
            return

        user = User(username=username, password_hash=hash_password(password))
        db.add(user)
        await db.commit()
        print(f"Пользователь '{username}' успешно создан.")


def main():
    parser = argparse.ArgumentParser(description="Создать пользователя финансового трекера")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    asyncio.run(create_user(args.username, args.password))


if __name__ == "__main__":
    main()
