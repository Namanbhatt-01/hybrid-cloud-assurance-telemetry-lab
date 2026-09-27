.PHONY: up down restart test impair heal logs clean status

all: test

up:
	@echo "Starting Lab 4 Observability Stack..."
	docker compose up -d --build

down:
	@echo "Stopping Lab 4 Stack..."
	docker compose down -v --remove-orphans

restart: down up

impair:
	@./impairment_injection/simulate_wan_degradation.sh lab4_mock_ai inject

heal:
	@./impairment_injection/simulate_wan_degradation.sh lab4_mock_ai heal

test: up
	@echo "Waiting for services and running end-to-end verification..."
	@sleep 10
	python3 prober/verify_assurance_pipeline.py

logs:
	docker compose logs -f

status:
	@docker compose ps
	@echo "\nPrometheus Targets:"
	@curl -s http://localhost:9090/api/v1/targets | jq . || true
	@echo "\nActive Alerts:"
	@curl -s http://localhost:9090/api/v1/alerts | jq . || true

clean:
	docker compose down -v --remove-orphans
