# Финансовый трекер — CLAUDE.md

## Язык проекта

Весь проект строго на **русском языке**: UI, сообщения об ошибках, типы данных (`доход`/`расход`), валидация, комментарии в коде.

## Архитектура

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0 async (aiosqlite), Alembic миграции
- **Frontend**: Vue 3 Composition API, Pinia, Vue Router, vue-chartjs, Axios
- **БД**: SQLite (async через aiosqlite)
- **Аутентификация**: JWT (access 15мин + refresh 7 дней в httpOnly cookie)
- **Деплой**: Docker Compose + Nginx reverse proxy + Certbot (Let's Encrypt)
- **Дополнительно**: Email MCP сервер (ExchangeLib) в корне репозитория

## Структура проекта

```
osnova/
├── docker-compose.yml          # Оркестрация всех сервисов
├── deploy/nginx/               # Nginx конфиги (finance.conf, email-mcp.conf)
├── finance/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py         # FastAPI app, lifespan, CORS, роутеры
│   │   │   ├── config.py       # Pydantic Settings (.env)
│   │   │   ├── database.py     # Async engine + sessionmaker
│   │   │   ├── dependencies.py # get_current_user, get_user_from_refresh_token
│   │   │   ├── models/         # SQLAlchemy модели (User, Category, Transaction)
│   │   │   ├── schemas/        # Pydantic v2 схемы
│   │   │   ├── routers/        # auth, categories, transactions, reports, project
│   │   │   └── services/       # auth (JWT), reports (агрегация), google_sheets
│   │   ├── alembic/            # Миграции БД
│   │   ├── tests/              # pytest-asyncio тесты (auth, categories, transactions, reports, load)
│   │   └── pyproject.toml
│   └── frontend/
│       ├── src/
│       │   ├── api/            # Axios клиент + API модули (auth, categories, transactions, reports, project)
│       │   ├── components/     # TransactionForm, TransactionTable, CategoryForm, AppHeader, charts/
│       │   ├── views/          # Dashboard, Transactions, Statistics, Project, Login
│       │   ├── stores/         # auth.js (JWT + refresh), finance.js (categories, transactions)
│       │   └── router/         # Vue Router с async guard (ждёт init перед проверкой auth)
│       ├── package.json
│       └── vite.config.js      # Proxy /api → localhost:8001
└── src/email_mcp/              # MCP сервер (не относится к финтрекеру)
```

## API эндпоинты (prefix: /api/v1)

| Роутер         | Путь                    | Описание                    |
|----------------|-------------------------|-----------------------------|
| auth           | POST /auth/login        | Вход (username + password)  |
| auth           | POST /auth/register     | Регистрация                 |
| auth           | POST /auth/refresh      | Обновление access token     |
| auth           | POST /auth/logout       | Выход (удаление cookie)     |
| categories     | GET/POST /categories    | Список / создание категорий |
| categories     | PUT/DELETE /categories/{id} | Обновление / удаление    |
| transactions   | GET/POST /transactions  | Список / создание           |
| transactions   | PUT/DELETE /transactions/{id} | Обновление / удаление  |
| reports        | GET /reports/balance    | Баланс (доход - расход)     |
| reports        | GET /reports/summary    | Сводка за период            |
| reports        | GET /reports/monthly-summary | Помесячная сводка       |
| reports        | GET /reports/category-breakdown | Разбивка по категориям |
| project        | GET /project/data       | Данные из Google Sheets     |
| project        | GET /project/summary    | Сводка по проекту           |

## Типы транзакций

В БД и API используются **русские** значения:
- `"доход"` — доход (income)
- `"расход"` — расход (expense)

Enum: `app/schemas/transaction.py → TransactionType`

## Запуск локально

### Backend
```bash
cd finance/backend
pip install fastapi uvicorn sqlalchemy alembic passlib[bcrypt] python-jose[cryptography] pydantic-settings aiosqlite
# Или: pip install -e . (может не работать из-за flat-layout проблемы с setuptools)
uvicorn app.main:app --reload --port 8001
```

### Frontend
```bash
cd finance/frontend
npm install
npm run dev
```

### Docker
```bash
docker compose up --build
```

## Тесты

```bash
cd finance/backend
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

## Ключевые решения и известные нюансы

1. **Async relationships**: Все SQLAlchemy relationship() используют `lazy="selectin"` для корректной работы в async-контексте
2. **datetime**: Используется `datetime.now(timezone.utc)` (не deprecated `utcnow()`)
3. **Google Sheets**: Синхронные вызовы обёрнуты в `asyncio.to_thread()` чтобы не блокировать event loop
4. **Auth refresh**: В auth store есть защита от race condition (общий `_refreshPromise`)
5. **Router guard**: Async, ждёт `authStore.init()` при первом переходе — не теряет сессию при F5
6. **CSS**: Классы строк таблицы — `type-income`/`type-expense` (не кириллические)
7. **pyproject.toml**: Editable install (`pip install -e .`) может не работать из-за `data/` и `alembic/` директорий. Обходной путь — установка зависимостей напрямую через pip

## Переменные окружения (.env)

```
DATABASE_URL=sqlite+aiosqlite:///./data/finance.db
JWT_SECRET_KEY=your-secret-key
GOOGLE_SERVICE_ACCOUNT_KEY=path/to/service-account.json
GOOGLE_SHEET_ID=your-sheet-id
CORS_ORIGINS=["http://localhost:5173"]
```
