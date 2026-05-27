# MetalCert — Сервис управления сертификатами металлопроката

Production-ready веб-сервис для хранения, OCR-распознавания и поиска сертификатов продукции металлопроката.

## Возможности

- **Загрузка сертификатов**: PDF, JPG, PNG, WEBP, TIFF — одиночно или массово с drag-and-drop
- **Автоматическое распознавание**: OCR (Tesseract + pdfplumber + PyMuPDF) + AI-парсер
- **Извлечение данных**: тип продукции, размер, марка стали, ГОСТ, номер/дата сертификата, производитель, партия
- **Умный поиск**: full-text (PostgreSQL tsvector) + fuzzy + ILIKE по всем полям
- **Ручное редактирование** с историей изменений (audit log)
- **Экспорт в Excel** результатов поиска
- **Дашборд** со статистикой и последними загрузками
- **Роли**: admin, manager, viewer
- **JWT авторизация** + rate limiting

## Стек

| Слой | Технологии |
|------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, React Query |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| OCR | Tesseract OCR (rus+eng), pdfplumber, PyMuPDF, OpenCV |
| Parser | Regex + rapidfuzz fuzzy matching |
| Queue | Celery + Redis |
| DB | PostgreSQL 16 с pg_trgm, tsvector |
| Proxy | Nginx |

## Требования

- Docker 24+
- Docker Compose v2+

## Быстрый старт

```bash
# 1. Клонировать / распаковать проект
cd certificates-service

# 2. Скопировать конфигурацию
cp .env.example .env
# При необходимости отредактируйте SECRET_KEY в .env

# 3. Собрать и запустить
docker-compose up -d --build

# 4. Применить миграции БД
docker-compose exec backend alembic upgrade head

# 5. Загрузить тестовые данные
docker-compose exec backend python seed_data.py
```

**Сервис доступен:** http://localhost

**API документация:** http://localhost/api/docs

## Логин по умолчанию

| Роль | Email | Пароль |
|------|-------|--------|
| Администратор | admin@example.com | admin123 |
| Менеджер | manager@example.com | manager123 |
| Наблюдатель | viewer@example.com | viewer123 |

> Смените пароли после первого входа!

## Управление

```bash
# Запуск
make up

# Остановка
make down

# Логи всех сервисов
make logs

# Логи отдельного сервиса
make logs-backend
make logs-worker

# Перезапуск воркера
make restart-worker

# Консоль базы данных
make shell-db

# Полная пересборка
make build
```

## Структура проекта

```
certificates-service/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # FastAPI routers
│   │   ├── core/               # Config, DB, Security, Celery
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # OCR, Parser, File services
│   │   └── workers/            # Celery tasks
│   ├── alembic/                # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/app/                # Next.js App Router pages
│   ├── src/components/         # React components
│   ├── src/hooks/              # Custom hooks
│   ├── src/lib/                # API client, auth utils
│   └── src/types/              # TypeScript types
├── nginx/
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── Makefile
```

## API Endpoints

| Метод | URL | Описание |
|-------|-----|----------|
| POST | /api/v1/auth/login | Вход |
| GET | /api/v1/auth/me | Текущий пользователь |
| POST | /api/v1/certificates/upload | Загрузить сертификат |
| GET | /api/v1/certificates | Список сертификатов |
| GET | /api/v1/certificates/{id} | Детали сертификата |
| PATCH | /api/v1/certificates/{id} | Редактировать |
| DELETE | /api/v1/certificates/{id} | Удалить |
| GET | /api/v1/certificates/{id}/file | Скачать файл |
| POST | /api/v1/certificates/{id}/reprocess | Переобработать |
| GET | /api/v1/search | Поиск по базе |
| GET | /api/v1/dashboard/stats | Статистика |
| GET | /api/v1/export/excel | Экспорт в Excel |

## Поиск — примеры запросов

```
120х120           → найдёт "Труба профильная 120х120х4"
труба 120         → найдёт все трубы с размером 120
Ст3               → все сертификаты марки Ст3
09Г2С             → по марке стали
ГОСТ 10704        → по ГОСТ
А500С 12          → арматура А500С диаметр 12 мм
ПАО Северсталь   → по производителю
```

## Поддерживаемые форматы

PDF, JPG, JPEG, PNG, WEBP, TIFF (до 50 МБ)

## Локальная разработка (без Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt

# Установить Tesseract OCR:
# Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-rus
# macOS: brew install tesseract tesseract-lang
# Windows: скачать с github.com/UB-Mannheim/tesseract/wiki

# Запустить PostgreSQL и Redis (через Docker или локально)
docker-compose up -d postgres redis

# Применить миграции
alembic upgrade head

# Запустить backend
uvicorn app.main:app --reload

# Celery worker (в отдельном терминале)
celery -A app.core.celery_app worker --loglevel=info

# Frontend
cd frontend
npm install
npm run dev
```

## Масштабирование

- Celery workers масштабируются горизонтально (`-c N` для N воркеров)
- PostgreSQL поддерживает миллионы записей (индексы настроены)
- Nginx обслуживает статику напрямую без нагрузки на backend
- Redis кэширует результаты Celery задач
