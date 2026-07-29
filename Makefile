.PHONY: all build up down restart logs shell test lint migrate psql help

all: build up

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart: down up

logs:
	docker compose logs -f

shell:
	docker compose exec app sh

psql:
	docker compose exec -e PGPASSWORD=postgres app psql -U postgres -h db -d contacts

test:
	docker compose exec app python -m pytest -v --tb=short

lint:
	docker compose exec app ruff check .

migrate:
	docker compose exec app alembic upgrade head

migrate-new:
	@read -p "Имя миграции: " name; \
	docker compose exec app alembic revision --autogenerate -m "$$name"

status:
	docker compose ps

prune:
	docker compose down -v

help:
	@echo "Использование: make <цель>"
	@echo ""
	@echo "Цели:"
	@echo "  build        Собрать Docker-образы"
	@echo "  up           Запустить сервисы в фоне"
	@echo "  down         Остановить сервисы"
	@echo "  restart      Перезапустить сервисы"
	@echo "  logs         Смотреть логи"
	@echo "  shell        Открыть shell в контейнере app"
	@echo "  psql         Открыть psql в БД contacts"
	@echo "  test         Запустить тесты"
	@echo "  lint         Запустить линтер"
	@echo "  migrate      Применить миграции Alembic"
	@echo "  migrate-new  Создать новую миграцию (запросит имя)"
	@echo "  status       Показать статус контейнеров"
	@echo "  prune        Остановить и удалить volumes (ВНИМАНИЕ: удалит данные)"
