# Тайный Санта - backend

Backend-приложение «Тайный Санта»: **Django + DRF + PostgreSQL + Redis + Docker**,
архитектура — модульный монолит (apps: `users`, `wishlists`, `events`, `chat`).


## Запуск через Docker (production-like: Postgres + Redis)

```bash
cp .env.example .env   # при необходимости подправить
docker compose up --build
```

- API: http://localhost:8000
- Health: http://localhost:8000/health
- Swagger: http://localhost:8000/api/schema/swagger-ui/
- WebSocket-чат пары: `ws://localhost:8000/ws/chat/<assignment_id>?token=<access>`

## Локальный запуск без Docker (SQLite + local-memory cache)

Настройки env-driven: если переменные `POSTGRES_*` / `REDIS_URL` пустые,
проект автоматически падает на SQLite и локальный кеш в памяти.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Демо-данные

```bash
python manage.py seed_superadmin   # суперадмин (+10000000000 / admin12345)
python manage.py seed_demo         # организатор + 4 юзера + мероприятие, готовое к жеребьёвке
```

`seed_demo` печатает id мероприятия; жеребьёвку запускает организатор
(`+12000000000 / demo12345`) через `POST /api/events/<id>/draw`.

## Роли и права (permission-based RBAC)

| Право | Пользователь | Организатор | Модератор | Суперадмин |
|---|:--:|:--:|:--:|:--:|
| Свои вишлисты / участие | ✓ | ✓ | ✓ | ✓ |
| Вести мероприятия | – | ✓ | – | ✓ |
| Читать чаты / отчёты | – | – | ✓ | ✓ |
| Управлять ролями | – | – | – | ✓ |

## Основные эндпоинты

- **Auth:** `POST /api/auth/{register,verify,login,token/refresh,logout}`
- **Профиль:** `GET|PATCH /api/profile`, `POST /api/profile/change-phone/{request,confirm}`
- **Пользователи (суперадмин):** `GET /api/users`, `PATCH /api/users/<id>/role`
- **Вишлисты:** `/api/wishlists[/<id>]`, items — `/api/wishlists/<id>/items[/<id>]`
- **Мероприятия:** `/api/events[/<id>]` + actions `join`, `participants`, `draw`,
  `complete`, `archive`, `gift-sent`, `my-assignment`
- **Чат:** WS `ws/chat/<assignment_id>?token=<access>`, история `GET /api/chat/<assignment_id>/messages`

Полная интерактивная схема — в Swagger UI (`/api/schema/swagger-ui/`).

