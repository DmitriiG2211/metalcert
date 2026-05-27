.PHONY: up down build migrate seed logs restart-worker shell-backend shell-db clean

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build --no-cache

start:
	docker-compose up -d --build

stop:
	docker-compose stop

migrate:
	docker-compose exec backend alembic upgrade head

migrate-down:
	docker-compose exec backend alembic downgrade -1

seed:
	docker-compose exec backend python seed_data.py

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-worker:
	docker-compose logs -f worker

logs-frontend:
	docker-compose logs -f frontend

restart-worker:
	docker-compose restart worker

shell-backend:
	docker-compose exec backend bash

shell-db:
	docker-compose exec postgres psql -U $${POSTGRES_USER:-certuser} -d $${POSTGRES_DB:-certificates_db}

shell-redis:
	docker-compose exec redis redis-cli

clean:
	docker-compose down -v --remove-orphans
	docker image prune -f

status:
	docker-compose ps

init: build
	docker-compose up -d postgres redis
	sleep 5
	docker-compose up -d backend worker frontend nginx
	sleep 10
	$(MAKE) migrate
	$(MAKE) seed
	@echo "Service started at http://localhost"
	@echo "API docs: http://localhost/api/docs"
	@echo "Default login: admin@example.com / admin123"
