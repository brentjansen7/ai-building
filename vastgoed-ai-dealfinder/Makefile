# Vastgoed AI Dealfinder — Makefile
.PHONY: help dev stop logs worker scheduler test install clean

help:
	@echo ""
	@echo "Vastgoed AI Dealfinder"
	@echo "======================"
	@echo "make dev       — Start alle services (API + DB + Redis)"
	@echo "make stop      — Stop alle services"
	@echo "make logs      — Toon logs"
	@echo "make worker    — Start RQ worker lokaal"
	@echo "make scheduler — Stel scheduled jobs in"
	@echo "make test      — Run tests"
	@echo "make install   — Installeer Python dependencies"
	@echo "make clean     — Verwijder Docker volumes"
	@echo ""

dev:
	cd deploy && docker-compose up -d
	@echo ""
	@echo "Services gestart:"
	@echo "  API:      http://localhost:8000"
	@echo "  API docs: http://localhost:8000/docs"
	@echo ""

stop:
	cd deploy && docker-compose down

logs:
	cd deploy && docker-compose logs -f --tail=100

logs-api:
	cd deploy && docker-compose logs -f api

logs-worker:
	cd deploy && docker-compose logs -f worker

worker:
	cd backend && python -m app.queue.worker

scheduler:
	cd backend && python -m app.queue.worker schedule

install:
	cd backend && pip install -r requirements.txt
	playwright install chromium

test:
	cd backend && pytest tests/ -v --tb=short

clean:
	cd deploy && docker-compose down -v
	@echo "Docker volumes verwijderd"

db-shell:
	docker exec -it vastgoed-postgres psql -U vastgoed_user -d vastgoed_ai

redis-cli:
	docker exec -it vastgoed-redis redis-cli
