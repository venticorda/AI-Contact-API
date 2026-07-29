# AI Contact API

Промышленный REST API для обработки контактных форм с AI-анализом
тональности, email-уведомлениями, PostgreSQL и Docker-инфраструктурой.

## О проекте

Сервис-презентация backend-разработчика: лендинг с контактной формой
и полноценным API. Каждое обращение проходит через AI-анализ тональности
(OpenAI GPT-4o-mini), сохраняется в PostgreSQL, дублируется email-уведомлениями
владельцу и отправителю. Встроенные метрики, rate limiting и health check.

Проект спроектирован по слоистой архитектуре (Routes → Services → Repositories),
с акцентом на обратную совместимость, graceful degradation и чистоту кода.

---

## Стек

| Компонент | Технология | Обоснование |
|-----------|-----------|-------------|
| Язык | **Python 3.14** | Асинхронность из коробки, читаемость, богатая экосистема |
| Фреймворк | **FastAPI** | Асинхронный, Pydantic v2, OpenAPI/docs автоматом |
| БД | **PostgreSQL 16** + SQLAlchemy 2.0 async | Надёжность, ACID, async sessions |
| AI | **OpenAI GPT-4o-mini** | Быстрая дешёвая модель, JSON-mode для структурированного вывода |
| Почта | **SMTP (Gmail)** с STARTTLS | Надёжная доставка, fallback если SMTP не настроен |
| Контейнеризация | **Docker Compose** (app + db + nginx) | Изолированная среда, production-ready |
| Тесты | **pytest** + pytest-asyncio + httpx | Асинхронные тесты, SQLite in-memory для CI |
| Линтер | **Ruff** | Быстрый, покрывает flake8/isort/pyupgrade |
| Миграции | **Alembic** | Версионирование схемы БД |
| CI | **GitHub Actions** | Автоматический lint + test на каждый push |

---

## Архитектура

### Структура проекта

```
backend/
├── app/
│   ├── ai/                    # AI-слой
│   │   ├── client.py          #   HTTP-клиент OpenAI API
│   │   └── service.py         #   Сервис с fallback
│   ├── api/
│   │   ├── routes/            # HTTP-эндпоинты
│   │   │   ├── health.py      #   GET /api/health
│   │   │   ├── metrics.py     #   GET /api/metrics
│   │   │   ├── contact.py     #   POST /api/contact
│   │   │   └── contacts.py    #   GET /api/contacts
│   │   └── schemas/           # Pydantic модели (request/response)
│   ├── core/                  # Конфигурация, логирование, исключения
│   │   ├── config.py          #   pydantic-settings (.env)
│   │   ├── exceptions.py      #   Кастомные HTTP-исключения
│   │   └── logging.py         #   Loguru (stdout + JSON в файлы)
│   ├── database/              # SQLAlchemy async engine + модели
│   │   ├── models.py          #   Contact (id, name, phone, email, ...)
│   │   └── session.py         #   Асинхронный engine + sessionmaker
│   ├── middlewares/           # Промежуточные слои
│   │   └── logging.py         #   Логирование каждого запроса
│   ├── repositories/          # Работа с данными (metrics, logs)
│   │   ├── metrics_repository.py
│   │   └── logs_repository.py
│   ├── services/              # Бизнес-логика
│   │   ├── contact_service.py #   Обработка контакта (AI → БД → email)
│   │   ├── email_service.py   #   SMTP-отправка (владельцу + копия)
│   │   └── rate_limit.py      #   Файловый rate limiter (5 запросов/мин)
│   ├── static/                # Фронтенд
│   │   ├── index.html
│   │   ├── style.css
│   │   └── script.js
│   ├── utils/                 # Вспомогательные функции
│   │   └── validators.py      #   Валидация телефона и email
│   └── main.py                # Точка входа, lifespan, middleware
├── tests/                     # pytest (14 тестов)
├── alembic/                   # Миграции БД
├── storage/                   # Файлы: логи, метрики, rate limit
├── .env                       # Переменные окружения
└── pyproject.toml             # Зависимости и инструменты

docker-compose.yml             # app + db + nginx
nginx/default.conf             # reverse proxy
Makefile                       # Команды для разработки
```

### Слоистая архитектура

```
HTTP (nginx) → Routes → Services → Repositories / AI / DB / SMTP
                ↑
          Middlewares (логирование, CORS)
```

**Routes** — только маршрутизация и вызов сервисов. Минимум логики.

**Services** — бизнес-логика: валидация → AI-анализ → сохранение в БД → email.
Координирует работу нескольких репозиториев/внешних сервисов.

**Repositories** — инкапсулируют доступ к данным (файлы, БД). Изолируют
бизнес-логику от деталей хранения.

**AI** — отдельный модуль с изолированным клиентом OpenAI. Service-прослойка
добавляет fallback: если AI недоступен, сервис возвращает `sentiment: "unknown"`
и продолжает работу.

### Почему FastAPI + PostgreSQL + Docker

- **FastAPI** — единственный Python-фреймворк, который даёт асинхронность,
Pydantic-валидацию и OpenAPI-документацию без дополнительных библиотек.
Синхронные альтернативы (Django/Flask) потребовали бы больше кода для
той же функциональности.

- **PostgreSQL** — выбран осознанно, чтобы показать работу с ACID-БД,
async SQLAlchemy и миграциями. SQLite подошёл бы для тестов, но не для
production-нагрузки.

- **Docker** — гарантирует одинаковое окружение на dev и production.
nginx front-proxy — стандартный production-паттерн для FastAPI.

---

## AI-интеграция

### Что делает

Единственная AI-функция — **анализ тональности** комментария из контактной
формы. Определяет emotion: `positive`, `neutral` или `negative`, и
возвращает краткое обоснование на русском.

### Промпт

```
Система:
  Ты ассистент анализа тональности текста.
  Определи тональность сообщения.
  Ответь в формате JSON с ключами 'sentiment'
  (один из: positive, neutral, negative)
  и 'reason' (краткое объяснение на русском).

Пользователь:
  {текст комментария}
```

- `temperature = 0.0` — детерминированный вывод
- `max_tokens = 150` — достаточно для JSON-ответа
- Модель: `gpt-4o-mini` — соотношение цена/скорость/качество

### Graceful fallback

AI-клиент обрабатывает все возможные ошибки:
- **HTTP 429** (Free tier rate limit) — пишет warning, fallback
- **ConnectError / TimeoutException** — сетевые проблемы
- **JSONDecodeError** — AI вернул невалидный JSON
- **Пустой API-ключ** — проверка на старте, даже не дёргает API

При любой ошибке сервис возвращает:
```json
{
  "sentiment": "unknown",
  "reason": "AI-анализ временно недоступен",
  "fallback_used": true
}
```

Основной бизнес-процесс (сохранение контакта, отправка email) выполняется
в любом случае. AI — не критическая зависимость, а дополнительная ценность.

---

## Что сделано с помощью AI

**Инструмент**: opencode — терминальный AI-ассистент (аналог Cursor в CLI).

### Принцип работы

AI выступал полноценным напарником: я задавал направление, AI предлагал
реализацию, вместе доводили до результата.

| Я | AI |
|---|---|
| Спроектировал архитектуру, выбрал стек, определил fallback-стратегию | Предложил структуру файлов, генерацию кода, шаблоны |
| Формулировал задачу с конкретными требованиями | Реализовал первую итерацию полностью |
| Проверял, отлаживал, переписывал узкие места | Анализировал ошибки, подсказывал варианты исправлений |

### Что генерировалось AI

- **Backend**: каркасы эндпоинтов, Pydantic-модели, вызовы сервисов
- **Frontend**: лендинг (HTML/CSS/JS) — ~95% через промпты, минимум правок
- **Infrastructure**: Dockerfile, docker-compose.yml, nginx.conf (шаблоны)
- **Миграции**: Alembic env.py + начальная миграция (под мою модель)
- **Тесты**: структура тестов, conftest, первая версия каждого теста
- **README**: первая версия, потом переписана под нужную структуру

### Примеры промптов

```
POST /api/contact — Pydantic Request, сервис-слой, в сервисе:
AI-анализ тональности, сохранение в PostgreSQL, два email.
Rate limiting — файловый, 5 запросов в минуту на IP.
Сделай каркас, я докручу обработку ошибок и fallback.
```

```
GET /api/health. Проверить: API отвечает, БД жива, AI-ключ настроен.
Вернуть статус, uptime, версию. Модель ответа — HealthResponse.
```

```
Docker Compose на три сервиса: Python-приложение (FastAPI),
PostgreSQL 16 Alpine, nginx Alpine reverse proxy. volume для данных БД
и storage приложения. healthcheck на db.
```

```
Лендинг: тёмная тема, фиолетовый акцент, форма обратной связи,
блок статусов (API/AI/БД), анимация появления при скролле, "пасхалки"-ссылки на мой GitHub и резюме на HH.
Стек: HTML + CSS + vanilla JS. Фиолетовый, ближе к сиреневому оттенку, фон тёмно-фиолетовый, ближе к чёрному.
```

### Что пришлось дорабатывать

- **Обработка ошибок OpenAI** — AI написал стандартный try/except, но free tier
  OpenAI возвращает 429. Вместе переписали: теперь тихо логируем и шлём fallback
- **Nginx → проксирование статики** — AI настроил прокси, но статика не
  отдавалась. Совместно разобрались и поправили маршрутизацию через app
- **Health check** — AI предложил реальный запрос к OpenAI. Переделали:
  health check проверяет только наличие ключа, не тратя лимиты
- **CSS-анимации фона** — несколько совместных итераций по подбору opacity,
  blur и timing, чтобы было видно, но не отвлекало

---

## Возможности

| Область | Что реализовано |
|---------|----------------|
| **API** | POST /api/contact с валидацией, GET /api/contacts с пагинацией, GET /api/health, GET /api/metrics |
| **AI** | Анализ тональности (positive/neutral/negative), graceful fallback при недоступности |
| **Email** | Уведомление владельцу + копия отправителю, HTML-письма, отключение если SMTP не настроен |
| **БД** | PostgreSQL 16, SQLAlchemy async, Alembic миграции |
| **Rate limit** | 5 запросов/мин на IP, файловое хранилище |
| **Логирование** | Loguru: цветной stdout + JSON в файлы (app, errors, AI) с ротацией |
| **Метрики** | JSON-файл: total, success, error, AI fallback count |
| **Frontend** | Лендинг-презентация, стек технологий, форма отправки, статусы API/AI/БД, scroll-анимация |
| **Безопасность** | Pydantic-валидация, CORS, rate limiting, глобальный error handler |
| **DevOps** | Docker Compose (3 контейнера), nginx reverse proxy, CI (GitHub Actions), pre-commit хуки |
| **Тесты** | 14 тестов: health, contact (success/validation/rate_limit), metrics, AI fallback, validators |

---

## Быстрый старт

```bash
git clone <repo-url> && cd <project>

cp backend/.env.example backend/.env
# Отредактировать backend/.env:
#   OPENAI_API_KEY=sk-your-key-here
#   SMTP_USER=your-email@gmail.com
#   SMTP_PASSWORD=your-app-password

docker compose up -d --build   # или make up

curl http://localhost/api/health
```

---

## Установка зависимостей

```bash
# Python + Poetry (обязательно)
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install poetry
poetry install

# Docker (альтернатива — не требует Poetry)
docker compose build     # соберёт образ со всеми зависимостями
```

---

## Команды

```bash
docker compose up -d --build    # Сборка и запуск
docker compose down             # Остановка
docker compose logs -f          # Логи всех контейнеров

docker compose exec app pytest -v --tb=short   # Тесты
docker compose exec app ruff check .           # Линтер
docker compose exec app alembic upgrade head   # Миграции

docker compose exec -e PGPASSWORD=postgres app psql \
  -U postgres -h db -d contacts               # Подключение к БД

docker compose restart nginx                   # Перезагрузка nginx
```

---

## API

Swagger-документация: `http://localhost/docs`

| Метод | Путь | Описание | Статусы |
|-------|------|----------|---------|
| GET | `/api/health` | Статус API, AI-сервиса и БД | 200 |
| GET | `/api/metrics` | Статистика обращений | 200 |
| GET | `/api/contacts?page=1&per_page=20` | Список контактов (пагинация) | 200 |
| POST | `/api/contact` | Отправить контактную форму | 200, 422, 429 |

### POST /api/contact

**Body:**
```json
{
  "name": "Иван Петров",
  "phone": "+79261234567",
  "email": "ivan@example.com",
  "comment": "Отличный сервис! Очень доволен работой."
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "name": "Иван Петров",
    "email": "ivan@example.com",
    "sentiment": "positive",
    "reason": "Пользователь выражает удовлетворение сервисом",
    "fallback_used": false
  }
}
```

**Response при недоступности AI:**
```json
{
  "success": true,
  "data": {
    "name": "Иван Петров",
    "email": "ivan@example.com",
    "sentiment": "unknown",
    "reason": "AI-анализ временно недоступен",
    "fallback_used": true
  }
}
```

**Response (422):**
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error" }
  ]
}
```

### Валидация (Pydantic v2)

| Поле | Правила |
|------|---------|
| `name` | 2–100 символов |
| `phone` | 7–15 цифр, опционально `+` в начале |
| `email` | Стандартный email-формат |
| `comment` | 10–3000 символов |

---

## Хранение данных

### PostgreSQL
- Таблица `contacts` — все отправленные формы
- UUID primary key, created_at, sentiment, reason, fallback_used
- SQLAlchemy async, Alembic-миграции

### Файловое хранилище (в `storage/`)
- **Логи** — JSON, ротация (1 файл/день, хранение 30 дней, gzip)
- **Метрики** — `metrics.json` (total_requests, successful_requests, error_requests, ai_fallback_count)
- **Rate limit** — JSON-файлы по IP, автоочистка устаревших записей

---

## Миграции

```bash
alembic upgrade head                         # Применить миграции
alembic revision --autogenerate -m "описание" # Новая миграция
alembic downgrade -1                         # Откат на шаг
alembic history                              # История миграций
```

---

## Переменные окружения

| Переменная | Описание | По умолчанию | Обязательно |
|-----------|----------|-------------|-------------|
| `OPENAI_API_KEY` | API-ключ OpenAI | — | Да (без AI — fallback) |
| `OPENAI_MODEL` | Модель OpenAI | `gpt-4o-mini` | — |
| `SMTP_HOST` | SMTP-сервер | `smtp.gmail.com` | Да (для email) |
| `SMTP_PORT` | Порт SMTP | `587` | — |
| `SMTP_USER` | Логин SMTP | — | Да |
| `SMTP_PASSWORD` | Пароль/App Password | — | Да |
| `SMTP_OWNER_EMAIL` | Email владельца для уведомлений | — | Да |
| `SMTP_FROM_EMAIL` | Отправитель писем | = SMTP_USER | — |
| `DATABASE_URL` | Подключение к БД | `postgresql+psycopg://postgres:postgres@localhost:5432/contacts` | — |
| `RATE_LIMIT_MAX` | Максимум запросов с одного IP | `5` | — |
| `RATE_LIMIT_WINDOW` | Временное окно rate limit (сек) | `60` | — |
| `DEBUG` | Режим отладки | `false` | — |

---

## CI/CD

### GitHub Actions

При каждом пуше в `master`:

```yaml
- Ruff check          # линтинг
- pytest -v           # 14 тестов, SQLite in-memory
```

Файл: `.github/workflows/ci.yml`

### Pre-commit

При каждом коммите — Ruff (линтер + форматтер):
```bash
pre-commit install   # установить хуки
pre-commit run -a    # проверить все файлы
```

---

## Лицензия

MIT
